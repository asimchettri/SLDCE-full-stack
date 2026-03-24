"""
ml_integration.py
-----------------
Bridge between FastAPI services and the SelfLearningCorrectionEngine.

Public functions:
  fit_dataset(db, dataset_id)
  detect_noise(db, dataset_id)
  apply_feedback(db, dataset_id, sample_id, previous_label,
                 updated_label, decision_type)
  run_learning_cycle(dataset_id)
  get_analytics(dataset_id)
  get_ml_integration()   ← kept for backward compat with baseline_service

Design:
  - All engine access goes through engine_registry (thread-safe, persistent)
  - Converts DB Sample objects → pandas DataFrame before calling engine
  - Maps backend vocabulary to engine vocabulary in one place
  - Services call these functions, never the engine directly
"""

import json
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.dataset import Sample
from services.engine_registry import get_engine_registry

logger = logging.getLogger(__name__)

# engine.apply_feedback expects: 'approve', 'reject', 'modify', 'uncertain'
DECISION_MAP = {
    "accept":  "approve",
    "approve": "approve",   
    "reject":  "reject",
    "modify":  "modify",
    "uncertain": "uncertain",
}


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _samples_to_dataframe(samples: List[Any]) -> pd.DataFrame:
    """
    Convert SQLAlchemy Sample objects to a pandas DataFrame.

    The engine expects:
      X : pd.DataFrame  — feature columns, index = sample.id
      y : pd.Series     — integer labels, same index

    Returns
    -------
    pd.DataFrame
        Columns: feature_0, feature_1, ..., feature_N, __label__
        Index:   sample.id values
    """
    rows = []
    indices = []

    for sample in samples:
        features = json.loads(sample.features)
        if isinstance(features, list):
            row = {f"feature_{i}": v for i, v in enumerate(features)}
        elif isinstance(features, dict):
            row = features
        else:
            logger.warning(f"Unexpected feature format for sample {sample.id}, skipping")
            continue

        row["__label__"] = sample.current_label
        rows.append(row)
        indices.append(sample.id)

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="No valid samples could be converted for ML processing"
        )

    df = pd.DataFrame(rows, index=indices)
    return df


def _df_to_X_y(df: pd.DataFrame):
    """Split DataFrame into feature matrix X and label series y."""
    y = df["__label__"]
    X = df.drop(columns=["__label__"])
    return X, y


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fit_dataset(db: Session, dataset_id: int) -> Dict[str, Any]:
    """
    Load all samples for dataset_id and fit a fresh engine.

    Call this:
      - When detection is run for the first time on a dataset
      - After a full dataset reload

    Parameters
    ----------
    db : Session
    dataset_id : int

    Returns
    -------
    Dict with keys: dataset_id, samples_fitted, classes
    """
    samples = db.query(Sample).filter(
        Sample.dataset_id == dataset_id
    ).all()

    if not samples or len(samples) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient samples to fit engine: "
                   f"{len(samples) if samples else 0} (minimum 10)"
        )

    df = _samples_to_dataframe(samples)
    X, y = _df_to_X_y(df)

    registry = get_engine_registry()

    with registry.lock(dataset_id):
        engine = registry.get_or_create(dataset_id)
        engine.fit(X, y)
        registry.save(dataset_id)

    logger.info(
        f"Engine fitted for dataset {dataset_id}: "
        f"{len(samples)} samples, classes={list(engine._ensemble.classes_)}"
    )

    return {
        "dataset_id": dataset_id,
        "samples_fitted": len(samples),
        "classes": [int(c) for c in engine._ensemble.classes_],
    }


def detect_noise(db: Session, dataset_id: int) -> Dict[str, Any]:
    """
    Run noise detection on all samples for dataset_id.

    Engine must be fitted first (call fit_dataset if not).

    Parameters
    ----------
    db : Session
    dataset_id : int

    Returns
    -------
    Dict from engine.detect_noise():
      flagged_samples: list of {sample_id, noise_probability,
                                predicted_label, original_label}
      current_threshold: float
    """
    registry = get_engine_registry()

    if not registry.is_fitted(dataset_id):
        logger.info(f"Engine not fitted for dataset {dataset_id}, fitting now")
        fit_dataset(db, dataset_id)

    samples = db.query(Sample).filter(
        Sample.dataset_id == dataset_id
    ).all()

    df = _samples_to_dataframe(samples)
    X, y = _df_to_X_y(df)

    with registry.lock(dataset_id):
        engine = registry.get(dataset_id)
        result = engine.detect_noise(X, y)

    logger.info(
        f"Detection complete for dataset {dataset_id}: "
        f"{len(result['flagged_samples'])} flagged, "
        f"threshold={result['current_threshold']:.3f}"
    )

    return result


def apply_feedback(
    db: Session,
    dataset_id: int,
    sample_id: int,
    previous_label: int,
    updated_label: int,
    decision_type: str,
    reviewer_comment: str = "",
    reviewer_confidence: float = 1.0,
) -> Dict[str, Any]:
    """
    Pass a human review decision to the engine.

    Translates backend vocabulary → engine vocabulary via DECISION_MAP.

    Parameters
    ----------
    db : Session
    dataset_id : int
    sample_id : int
        Must match an index value used during detect_noise().
    previous_label : int
    updated_label : int
    decision_type : str
        Backend vocabulary: 'approve', 'reject', 'modify', 'uncertain'
    reviewer_comment : str
    reviewer_confidence : float

    Returns
    -------
    Dict — the stored FeedbackRecord as a dict
    """
    registry = get_engine_registry()

    if not registry.is_fitted(dataset_id):
        raise HTTPException(
            status_code=400,
            detail=f"Engine for dataset {dataset_id} is not fitted. "
                   f"Run detection first."
        )

    # Translate vocabulary
    engine_decision = DECISION_MAP.get(decision_type)
    if engine_decision is None:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision_type '{decision_type}'. "
                   f"Must be one of: {list(DECISION_MAP.keys())}"
        )

    with registry.lock(dataset_id):
        engine = registry.get(dataset_id)
        record = engine.apply_feedback(
            sample_id=sample_id,
            previous_label=previous_label,
            updated_label=updated_label,
            decision_type=engine_decision,
            reviewer_comment=reviewer_comment,
            reviewer_confidence=reviewer_confidence,
        )
        registry.save(dataset_id)

    logger.info(
        f"Feedback applied: dataset={dataset_id}, sample={sample_id}, "
        f"decision={engine_decision}"
    )

    return record


def run_learning_cycle(dataset_id: int) -> Dict[str, Any]:
    """
    Run one full learning cycle on the engine:
      1. update_meta_model()  — retrain meta-model on feedback
      2. update_threshold()   — adapt decision threshold
      3. retrain_if_ready()   — retrain ensemble if enough corrections

    Call this from retrain_service after corrections are applied.

    Parameters
    ----------
    dataset_id : int

    Returns
    -------
    Dict with keys: meta_model, threshold, retrain
    """
    registry = get_engine_registry()

    if not registry.is_fitted(dataset_id):
        raise HTTPException(
            status_code=400,
            detail=f"Engine for dataset {dataset_id} is not fitted."
        )

    with registry.lock(dataset_id):
        engine = registry.get(dataset_id)

        meta_result = engine.update_meta_model()
        threshold_result = engine.update_threshold()
        retrain_result = engine.retrain_if_ready()

        registry.save(dataset_id)

    logger.info(
        f"Learning cycle complete for dataset {dataset_id}: "
        f"meta_trained={meta_result['trained']}, "
        f"retrained={retrain_result['retrained']}"
    )

    return {
        "dataset_id": dataset_id,
        "meta_model": meta_result,
        "threshold": threshold_result,
        "retrain": retrain_result,
    }


def get_analytics(dataset_id: int) -> Dict[str, Any]:
    """
    Return longitudinal analytics from the engine.

    Parameters
    ----------
    dataset_id : int

    Returns
    -------
    Dict from engine.get_analytics()
    """
    registry = get_engine_registry()
    engine = registry.get(dataset_id)

    if engine is None:
        return {
            "dataset_id": dataset_id,
            "message": "No engine found for this dataset. Run detection first.",
            "history": []
        }

    return engine.get_analytics()


def get_engine_status(dataset_id: int) -> Dict[str, Any]:
    """
    Return registry status for a dataset's engine.
    Useful for health checks and debug endpoints.

    Parameters
    ----------
    dataset_id : int
    """
    registry = get_engine_registry()
    return registry.status(dataset_id)


# ---------------------------------------------------------------------------
# Backward compatibility shim
# ---------------------------------------------------------------------------


class _LegacyMLIntegration:
    """
    Minimal shim so baseline_service.py doesn't crash before Day 3.
    Only implements evaluate_model() which is the one method it uses.
    """

    def evaluate_model(
        self,
        X: np.ndarray,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, float]:
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
        )
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(
                precision_score(y_true, y_pred, average="weighted", zero_division=0)
            ),
            "recall": float(
                recall_score(y_true, y_pred, average="weighted", zero_division=0)
            ),
            "f1_score": float(
                f1_score(y_true, y_pred, average="weighted", zero_division=0)
            ),
        }


_legacy_instance: Optional[_LegacyMLIntegration] = None


def get_ml_integration() -> _LegacyMLIntegration:
    """
    Backward-compat shim for baseline_service.py.
    Will be removed when baseline_service is rewritten on Day 3.
    """
    global _legacy_instance
    if _legacy_instance is None:
        _legacy_instance = _LegacyMLIntegration()
    return _legacy_instance