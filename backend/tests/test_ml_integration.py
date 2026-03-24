"""
test_ml_integration.py
----------------------
Unit tests for services/ml_integration.py

Tests:
  - test_fit_dataset_with_valid_samples
  - test_detect_noise_returns_flagged_samples
  - test_apply_feedback_translates_vocabulary
  - test_run_learning_cycle_completes
"""

import json
from typing import List
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.dataset import Sample
from services import ml_integration
from services.ml_integration import (
    DECISION_MAP,
    apply_feedback,
    detect_noise,
    fit_dataset,
    run_learning_cycle,
)

DATASET_ID = 99  # matches conftest.py


# ── Helpers ──────────────────────────────────────────────────────────────────

def _insert_samples(db: Session, dataset_id: int, n: int = 60,
                    noise_pct: float = 0.0, seed: int = 42) -> List[Sample]:
    """
    Insert n samples into the in-memory DB.
    noise_pct fraction of samples get current_label flipped to simulate noise.
    """
    rng = np.random.RandomState(seed)
    X = rng.randn(n, 4)
    y = (np.arange(n) % 3)

    samples = []
    for i, (features, label) in enumerate(zip(X.tolist(), y.tolist())):
        current = label
        if rng.random() < noise_pct:
            current = (label + 1) % 3          # flip label
        s = Sample(
            dataset_id=dataset_id,
            sample_index=i,
            features=json.dumps(features),
            original_label=int(label),
            current_label=int(current),
            is_suspicious=False,
            is_corrected=False,
        )
        db.add(s)
        samples.append(s)
    db.commit()
    for s in samples:
        db.refresh(s)
    return samples


# ── fit_dataset ───────────────────────────────────────────────────────────────

class TestFitDataset:
    def test_fit_dataset_with_valid_samples(
        self, db: Session, tmp_registry
    ):
        """
        fit_dataset() must fit the engine and return the expected keys.
        After the call the registry must report the engine as fitted.
        """
        _insert_samples(db, DATASET_ID, n=60)

        result = fit_dataset(db, DATASET_ID)

        assert result["dataset_id"] == DATASET_ID
        assert result["samples_fitted"] == 60
        assert isinstance(result["classes"], list)
        assert len(result["classes"]) == 3          # 3 classes in fixture data
        assert tmp_registry.is_fitted(DATASET_ID)

    def test_fit_dataset_raises_on_too_few_samples(
        self, db: Session, tmp_registry
    ):
        """fit_dataset() must raise HTTP 400 when fewer than 10 samples exist."""
        _insert_samples(db, DATASET_ID, n=5)

        with pytest.raises(HTTPException) as exc_info:
            fit_dataset(db, DATASET_ID)

        assert exc_info.value.status_code == 400
        assert "Insufficient" in exc_info.value.detail

    def test_fit_dataset_raises_on_empty_dataset(
        self, db: Session, tmp_registry
    ):
        """fit_dataset() must raise HTTP 400 when the dataset has no samples."""
        with pytest.raises(HTTPException) as exc_info:
            fit_dataset(db, DATASET_ID)

        assert exc_info.value.status_code == 400

    def test_fit_dataset_saves_engine_to_disk(
        self, db: Session, tmp_registry, tmp_path
    ):
        """fit_dataset() must persist the engine via registry.save()."""
        _insert_samples(db, DATASET_ID, n=60)

        fit_dataset(db, DATASET_ID)

        path = tmp_registry._engine_path(DATASET_ID)
        assert path.exists(), f"Expected engine file at {path}"


# ── detect_noise ──────────────────────────────────────────────────────────────

class TestDetectNoise:
    def test_detect_noise_returns_flagged_samples(
        self, db: Session, tmp_registry
    ):
        """
        detect_noise() must return a dict with 'flagged_samples' and
        'current_threshold'. Each flagged sample must have the required keys.
        """
        _insert_samples(db, DATASET_ID, n=150, noise_pct=0.15)
        fit_dataset(db, DATASET_ID)

        result = detect_noise(db, DATASET_ID)

        assert "flagged_samples" in result
        assert "current_threshold" in result
        assert isinstance(result["flagged_samples"], list)
        assert isinstance(result["current_threshold"], float)

        if result["flagged_samples"]:
            sample = result["flagged_samples"][0]
            assert "sample_id" in sample
            assert "noise_probability" in sample
            assert "predicted_label" in sample
            assert "original_label" in sample

    def test_detect_noise_auto_fits_if_not_fitted(
        self, db: Session, tmp_registry
    ):
        """
        detect_noise() must auto-call fit_dataset() when the engine
        is not yet fitted — no manual fit required.
        """
        _insert_samples(db, DATASET_ID, n=60)

        # Do NOT call fit_dataset first
        result = detect_noise(db, DATASET_ID)

        assert "flagged_samples" in result
        assert tmp_registry.is_fitted(DATASET_ID)

    def test_detect_noise_noise_probabilities_in_range(
        self, db: Session, tmp_registry
    ):
        """All noise_probability values must be in [0.0, 1.0]."""
        _insert_samples(db, DATASET_ID, n=150, noise_pct=0.15)
        fit_dataset(db, DATASET_ID)

        result = detect_noise(db, DATASET_ID)

        for fs in result["flagged_samples"]:
            assert 0.0 <= fs["noise_probability"] <= 1.0, (
                f"noise_probability out of range: {fs['noise_probability']}"
            )

    def test_detect_noise_threshold_is_positive(
        self, db: Session, tmp_registry
    ):
        """current_threshold must be a positive float."""
        _insert_samples(db, DATASET_ID, n=60)
        fit_dataset(db, DATASET_ID)

        result = detect_noise(db, DATASET_ID)

        assert result["current_threshold"] > 0.0


# ── apply_feedback ────────────────────────────────────────────────────────────

class TestApplyFeedback:
    def _setup_and_get_flagged(self, db: Session, tmp_registry):
        """Fit, detect, return first flagged sample_id."""
        _insert_samples(db, DATASET_ID, n=150, noise_pct=0.20)
        fit_dataset(db, DATASET_ID)
        result = detect_noise(db, DATASET_ID)

        flagged = result["flagged_samples"]
        if not flagged:
            pytest.skip("No flagged samples — can't test apply_feedback")

        return flagged[0]

    def test_apply_feedback_translates_vocabulary(
        self, db: Session, tmp_registry
    ):
        """
        apply_feedback() must translate 'accept' → 'approve' before
        passing to the engine. The returned record must reflect the
        engine vocabulary, not the backend vocabulary.
        """
        flagged = self._setup_and_get_flagged(db, tmp_registry)
        sid = flagged["sample_id"]
        prev = flagged["original_label"]
        upd = flagged["predicted_label"]

        record = apply_feedback(
            db=db,
            dataset_id=DATASET_ID,
            sample_id=sid,
            previous_label=prev,
            updated_label=upd,
            decision_type="accept",        # backend vocabulary
        )

        # Engine stores 'approve', not 'accept'
        assert record["decision_type"] == "approve"
        assert record["sample_id"] == sid

    def test_apply_feedback_reject_passthrough(
        self, db: Session, tmp_registry
    ):
        """'reject' maps to 'reject' (same in both vocabularies)."""
        flagged = self._setup_and_get_flagged(db, tmp_registry)
        sid = flagged["sample_id"]
        prev = flagged["original_label"]

        record = apply_feedback(
            db=db,
            dataset_id=DATASET_ID,
            sample_id=sid,
            previous_label=prev,
            updated_label=prev,
            decision_type="reject",
        )

        assert record["decision_type"] == "reject"

    def test_apply_feedback_modify_passthrough(
        self, db: Session, tmp_registry
    ):
        """'modify' maps to 'modify' (same in both vocabularies)."""
        flagged = self._setup_and_get_flagged(db, tmp_registry)
        sid = flagged["sample_id"]
        prev = flagged["original_label"]
        new_label = (int(prev) + 1) % 3

        record = apply_feedback(
            db=db,
            dataset_id=DATASET_ID,
            sample_id=sid,
            previous_label=prev,
            updated_label=new_label,
            decision_type="modify",
        )

        assert record["decision_type"] == "modify"

    def test_apply_feedback_invalid_decision_raises_400(
        self, db: Session, tmp_registry
    ):
        """Unknown decision_type must raise HTTP 400."""
        flagged = self._setup_and_get_flagged(db, tmp_registry)
        sid = flagged["sample_id"]

        with pytest.raises(HTTPException) as exc_info:
            apply_feedback(
                db=db,
                dataset_id=DATASET_ID,
                sample_id=sid,
                previous_label=flagged["original_label"],
                updated_label=flagged["predicted_label"],
                decision_type="banana",           # invalid
            )

        assert exc_info.value.status_code == 400
        assert "Invalid decision_type" in exc_info.value.detail

    def test_apply_feedback_raises_400_if_engine_not_fitted(
        self, db: Session, tmp_registry
    ):
        """apply_feedback() must raise HTTP 400 if engine has not been fitted."""
        # No fit_dataset call
        with pytest.raises(HTTPException) as exc_info:
            apply_feedback(
                db=db,
                dataset_id=DATASET_ID,
                sample_id=1,
                previous_label=0,
                updated_label=1,
                decision_type="accept",
            )

        assert exc_info.value.status_code == 400
        assert "not fitted" in exc_info.value.detail.lower()

    def test_decision_map_covers_all_expected_keys(self):
        """DECISION_MAP must contain all four backend decision types."""
        expected = {"accept", "approve", "reject", "modify", "uncertain"}
        assert set(DECISION_MAP.keys()) == expected


# ── run_learning_cycle ────────────────────────────────────────────────────────

class TestRunLearningCycle:
    def test_run_learning_cycle_completes(
        self, db: Session, tmp_registry
    ):
        """
        run_learning_cycle() must complete without raising and return
        a dict with the expected top-level keys.
        """
        _insert_samples(db, DATASET_ID, n=150, noise_pct=0.15)
        fit_dataset(db, DATASET_ID)
        detect_noise(db, DATASET_ID)

        result = run_learning_cycle(DATASET_ID)

        assert result["dataset_id"] == DATASET_ID
        assert "meta_model" in result
        assert "threshold" in result
        assert "retrain" in result

    def test_run_learning_cycle_meta_model_keys(
        self, db: Session, tmp_registry
    ):
        """meta_model sub-dict must contain 'trained' and 'feedback_count'."""
        _insert_samples(db, DATASET_ID, n=60)
        fit_dataset(db, DATASET_ID)
        detect_noise(db, DATASET_ID)

        result = run_learning_cycle(DATASET_ID)

        assert "trained" in result["meta_model"]
        assert "feedback_count" in result["meta_model"]
        assert isinstance(result["meta_model"]["trained"], bool)

    def test_run_learning_cycle_threshold_keys(
        self, db: Session, tmp_registry
    ):
        """threshold sub-dict must contain previous and new threshold values."""
        _insert_samples(db, DATASET_ID, n=60)
        fit_dataset(db, DATASET_ID)
        detect_noise(db, DATASET_ID)

        result = run_learning_cycle(DATASET_ID)

        thresh = result["threshold"]
        assert "previous_threshold" in thresh
        assert "new_threshold" in thresh
        assert "correction_precision" in thresh
        assert isinstance(thresh["previous_threshold"], float)
        assert isinstance(thresh["new_threshold"], float)

    def test_run_learning_cycle_retrain_keys(
        self, db: Session, tmp_registry
    ):
        """retrain sub-dict must contain 'retrained' bool and 'corrections_applied'."""
        _insert_samples(db, DATASET_ID, n=60)
        fit_dataset(db, DATASET_ID)
        detect_noise(db, DATASET_ID)

        result = run_learning_cycle(DATASET_ID)

        retrain = result["retrain"]
        assert "retrained" in retrain
        assert "corrections_applied" in retrain
        assert isinstance(retrain["retrained"], bool)

    def test_run_learning_cycle_raises_400_if_not_fitted(
        self, db: Session, tmp_registry
    ):
        """run_learning_cycle() must raise HTTP 400 if engine is not fitted."""
        with pytest.raises(HTTPException) as exc_info:
            run_learning_cycle(DATASET_ID)

        assert exc_info.value.status_code == 400
        assert "not fitted" in exc_info.value.detail.lower()

    def test_run_learning_cycle_saves_engine(
        self, db: Session, tmp_registry
    ):
        """run_learning_cycle() must persist updated engine state to disk."""
        _insert_samples(db, DATASET_ID, n=60)
        fit_dataset(db, DATASET_ID)
        detect_noise(db, DATASET_ID)

        run_learning_cycle(DATASET_ID)

        path = tmp_registry._engine_path(DATASET_ID)
        assert path.exists(), "Engine was not saved after learning cycle"