"""
benchmark_service.py
--------------------
Runs benchmark comparisons between SLDCE, Cleanlab, random correction,
and no-correction baselines.

Public methods:
    run_sldce_benchmark(db, dataset_id, iterations)
    run_cleanlab_benchmark(db, dataset_id)
    run_random_benchmark(db, dataset_id)
    run_no_correction_benchmark(db, dataset_id)
    get_benchmark_results(db, dataset_id)
"""

import json
import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import cross_val_predict
from sqlalchemy.orm import Session

from models.dataset import BenchmarkResult, Sample
from services.dataset_service import DatasetService
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from services.ml_integration import (
    apply_feedback,
    detect_noise,
    fit_dataset,
    run_learning_cycle,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_X_y(db: Session, dataset_id: int):
    """
    Load all samples for dataset_id and return (X, y) as numpy arrays.
    X shape: (n_samples, n_features)
    y shape: (n_samples,)
    """
    samples = (
        db.query(Sample)
        .filter(Sample.dataset_id == dataset_id)
        .order_by(Sample.sample_index)
        .all()
    )

    if not samples:
        raise HTTPException(
            status_code=404,
            detail=f"No samples found for dataset {dataset_id}"
        )

    X_rows = []
    y_rows = []
    sample_ids = []

    for s in samples:
        features = json.loads(s.features)
        if isinstance(features, list):
            X_rows.append(features)
        else:
            X_rows.append(list(features.values()))
        y_rows.append(s.current_label)
        sample_ids.append(s.id)

    X = np.array(X_rows, dtype=float)
    y = np.array(y_rows, dtype=int)

    return X, y, sample_ids


def _train_and_score(X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Train a RandomForest with cross-validation and return metrics.
    Uses 5-fold CV so we don't need a separate test set.
    """
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)

    # Cross-validated predictions for scoring
    y_pred = cross_val_predict(clf, X, y, cv=min(5, len(np.unique(y))))

    return {
        "accuracy": float(accuracy_score(y, y_pred)),
        "precision": float(
            precision_score(y, y_pred, average="weighted", zero_division=0)
        ),
        "recall": float(
            recall_score(y, y_pred, average="weighted", zero_division=0)
        ),
        "f1": float(
            f1_score(y, y_pred, average="weighted", zero_division=0)
        ),
    }


def _get_pred_probs(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Get out-of-fold predicted probabilities using cross_val_predict.
    Required by Cleanlab's find_label_issues.
    """
    from sklearn.model_selection import StratifiedKFold

    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    n_splits = min(5, len(np.unique(y)))

    pred_probs = cross_val_predict(
        clf, X, y,
        cv=StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42),
        method="predict_proba"
    )
    return pred_probs


def _save_result(
    db: Session,
    dataset_id: int,
    tool: str,
    iteration: int,
    metrics: Dict[str, float],
    human_effort: int = None,
    meta: Dict = None,
) -> BenchmarkResult:
    """Persist one benchmark result row."""
    result = BenchmarkResult(
        dataset_id=dataset_id,
        tool=tool,
        iteration=iteration,
        precision=metrics.get("precision"),
        recall=metrics.get("recall"),
        accuracy=metrics.get("accuracy"),
        f1=metrics.get("f1"),
        human_effort=human_effort,
        meta=json.dumps(meta) if meta else None,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    logger.info(
        f"Saved benchmark: dataset={dataset_id}, tool={tool}, "
        f"iter={iteration}, accuracy={metrics.get('accuracy', 0):.4f}"
    )
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_no_correction_benchmark(db: Session, dataset_id: int) -> Dict[str, Any]:
    """
    Baseline: train on the raw noisy dataset with zero corrections.
    Represents the worst-case starting point.
    """
    logger.info(f"Running no-correction benchmark for dataset {dataset_id}")

    X, y, _ = _get_X_y(db, dataset_id)
    metrics = _train_and_score(X, y)

    _save_result(
        db, dataset_id,
        tool="no_correction",
        iteration=1,
        metrics=metrics,
        meta={"num_samples": len(y), "num_classes": len(np.unique(y))},
    )

    return {"tool": "no_correction", "iteration": 1, **metrics}


def run_random_benchmark(db: Session, dataset_id: int) -> Dict[str, Any]:
    """
    Baseline: randomly flag X% of samples (matching SLDCE detection rate)
    and randomly assign corrected labels.
    Measures how much random correction helps vs SLDCE.
    """
    logger.info(f"Running random correction benchmark for dataset {dataset_id}")

    X, y, sample_ids = _get_X_y(db, dataset_id)
    classes = np.unique(y)

    # Match the typical SLDCE detection rate (~15%)
    detection_rate = 0.15
    n_flag = max(1, int(len(y) * detection_rate))

    rng = np.random.RandomState(42)
    flagged_indices = rng.choice(len(y), size=n_flag, replace=False)

    # Randomly assign a different label to flagged samples
    y_corrected = y.copy()
    for idx in flagged_indices:
        other_classes = classes[classes != y[idx]]
        if len(other_classes) > 0:
            y_corrected[idx] = rng.choice(other_classes)

    metrics = _train_and_score(X, y_corrected)

    _save_result(
        db, dataset_id,
        tool="random",
        iteration=1,
        metrics=metrics,
        human_effort=n_flag,
        meta={
            "num_flagged": n_flag,
            "flag_rate": detection_rate,
            "num_samples": len(y),
        },
    )

    return {"tool": "random", "iteration": 1, "human_effort": n_flag, **metrics}


def run_cleanlab_benchmark(db: Session, dataset_id: int) -> Dict[str, Any]:
    """
    Run Cleanlab's find_label_issues on the dataset.
    Removes flagged samples and retrains — Cleanlab's standard approach.

    Returns metrics + number of issues found.
    """
    logger.info(f"Running Cleanlab benchmark for dataset {dataset_id}")

    try:
        from cleanlab.filter import find_label_issues
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Cleanlab is not installed. Run: pip install cleanlab"
        )

    X, y, _ = _get_X_y(db, dataset_id)

    # Step 1: Get out-of-fold predicted probabilities
    logger.info("Computing out-of-fold predicted probabilities for Cleanlab...")
    pred_probs = _get_pred_probs(X, y)

    # Step 2: Find label issues
    issue_indices = find_label_issues(
        labels=y,
        pred_probs=pred_probs,
        return_indices_ranked_by="self_confidence",
    )

    num_issues = len(issue_indices)
    logger.info(f"Cleanlab found {num_issues} label issues")

    # Step 3: Remove flagged samples (Cleanlab's default approach)
    mask = np.ones(len(y), dtype=bool)
    mask[issue_indices] = False

    X_clean = X[mask]
    y_clean = y[mask]

    if len(X_clean) < 10:
        raise HTTPException(
            status_code=400,
            detail="Too many samples removed by Cleanlab — dataset too small or too noisy"
        )

    metrics = _train_and_score(X_clean, y_clean)

    _save_result(
        db, dataset_id,
        tool="cleanlab",
        iteration=1,
        metrics=metrics,
        human_effort=num_issues,
        meta={
            "num_issues_found": num_issues,
            "issue_rate": round(num_issues / len(y), 4),
            "samples_removed": num_issues,
            "samples_remaining": int(mask.sum()),
        },
    )

    return {
        "tool": "cleanlab",
        "iteration": 1,
        "num_issues_found": num_issues,
        "human_effort": num_issues,
        **metrics,
    }

def run_sldce_benchmark(
    db: Session,
    dataset_id: int,
    iterations: int = 5,
) -> List[Dict[str, Any]]:
    """
    Run the full SLDCE loop for N iterations using ensemble disagreement
    as the correction signal (bypasses untrained meta-model).

    Each iteration:
      1. Train RandomForest on current labels
      2. Find samples where model strongly disagrees with current label
      3. Correct those samples (simulated human accepts high-confidence fixes)
      4. Score the corrected dataset
    """
    logger.info(
        f"Running SLDCE benchmark for dataset {dataset_id}, "
        f"{iterations} iterations"
    )

    results = []
    modified_sample_ids = set()

    for iteration in range(1, iterations + 1):
        logger.info(f"--- SLDCE Iteration {iteration}/{iterations} ---")

        X, y, sample_ids = _get_X_y(db, dataset_id)
        classes = np.unique(y)
        n_splits = min(5, len(classes))

        # Step 1: Get out-of-fold predicted probabilities
        clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        from sklearn.model_selection import StratifiedKFold, cross_val_predict
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        pred_probs = cross_val_predict(clf, X, y, cv=skf, method="predict_proba")
        predictions = classes[np.argmax(pred_probs, axis=1)]

        # Step 2: Compute noise signal per sample
        # noise_score = 1 - P(current_label) — how confident model is that
        # the current label is WRONG
        noise_scores = np.array([
            1.0 - pred_probs[i, list(classes).index(y[i])]
            for i in range(len(y))
        ])

        # Dynamic threshold: start permissive, get stricter each iteration
        threshold = min(0.3 + (iteration - 1) * 0.1, 0.7)
        logger.info(f"  Noise threshold: {threshold:.2f}")

        # Step 3: Flag and auto-correct high-confidence disagreements
        flagged = 0
        accepted = 0
        rejected = 0

        samples_db = (
            db.query(Sample)
            .filter(Sample.dataset_id == dataset_id)
            .order_by(Sample.sample_index)
            .all()
        )
        sample_map = {s.id: s for s in samples_db}

      

        # Inside the correction loop, track modifications
        for i, sid in enumerate(sample_ids):
            if noise_scores[i] >= threshold:
                flagged += 1
                predicted = predictions[i]
                current = y[i]
                if predicted != current:
                    sample = sample_map.get(sid)
                    if sample:
                        modified_sample_ids.add(sid)
                        sample.current_label = int(predicted)
                        sample.is_corrected = True
                        sample.is_suspicious = True
                    accepted += 1
                else:
                    rejected += 1
                    
        db.commit()
        logger.info(f"  Flagged: {flagged}, Accepted: {accepted}, Rejected: {rejected}")

        # Step 4: Score corrected dataset
        X_new, y_new, _ = _get_X_y(db, dataset_id)
        metrics = _train_and_score(X_new, y_new)

        # Save to DB
        _save_result(
            db, dataset_id,
            tool="sldce",
            iteration=iteration,
            metrics=metrics,
            human_effort=flagged,
            meta={
                "flagged": flagged,
                "accepted": accepted,
                "rejected": rejected,
                "threshold_used": round(threshold, 2),
            },
        )

        iter_result = {
            "tool": "sldce",
            "iteration": iteration,
            "flagged": flagged,
            "accepted": accepted,
            "rejected": rejected,
            "human_effort": flagged,
            **metrics,
        }
        results.append(iter_result)
        logger.info(f"  Iteration {iteration} accuracy: {metrics['accuracy']:.4f}")

    if modified_sample_ids:
        samples_to_restore = db.query(Sample).filter(
            Sample.id.in_(modified_sample_ids)
        ).all()
        for s in samples_to_restore:
            s.current_label = s.original_label
            s.is_corrected = False
            s.is_suspicious = False
        db.commit()
        logger.info(
            f"Restored {len(modified_sample_ids)} benchmark-modified samples "
            f"for dataset {dataset_id}"
        )

    return results

def get_benchmark_results(
    db: Session, dataset_id: int
) -> List[Dict[str, Any]]:
    """
    Fetch all stored benchmark results for a dataset.

    Returns
    -------
    List of benchmark result dicts, ordered by tool then iteration.
    """
    results = (
        db.query(BenchmarkResult)
        .filter(BenchmarkResult.dataset_id == dataset_id)
        .order_by(BenchmarkResult.tool, BenchmarkResult.iteration)
        .all()
    )

    return [
        {
            "id": r.id,
            "dataset_id": r.dataset_id,
            "tool": r.tool,
            "iteration": r.iteration,
            "precision": r.precision,
            "recall": r.recall,
            "accuracy": r.accuracy,
            "f1": r.f1,
            "human_effort": r.human_effort,
            "meta": json.loads(r.meta) if r.meta else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in results
    ]



