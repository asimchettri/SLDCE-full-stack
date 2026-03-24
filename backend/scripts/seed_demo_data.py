"""
seed_demo_data.py
-----------------
Creates a clean demo dataset for SLDCE demonstrations.

What it does:
  1. Creates a demo dataset (500 samples, 5 features, 3 classes)
  2. Injects 15% label noise
  3. Runs detection via the ML engine
  4. Simulates 20 feedback records (mix of approve/reject/modify)
  5. Applies corrections
  6. Retrains the engine once

Usage:
    python scripts/seed_demo_data.py
    python scripts/seed_demo_data.py --reset   # deletes existing demo dataset first
    python scripts/seed_demo_data.py --name "My Demo"
"""

import sys
import os
import json
import random
import argparse
import logging
import numpy as np
from pathlib import Path
from datetime import datetime,timezone

# ── Make sure backend root is on the path ────────────────────────────────────
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from core.database import SessionLocal
from models.dataset import Dataset, Sample, Detection, Suggestion, Feedback
from models.model import MLModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("seed")

# ── Constants ─────────────────────────────────────────────────────────────────
DEMO_NAME        = "Demo Dataset (Iris-like)"
N_SAMPLES        = 500
N_FEATURES       = 5
N_CLASSES        = 3
NOISE_RATE       = 0.15          # 15% label noise
N_FEEDBACK       = 20            # feedback records to simulate
RANDOM_SEED      = 42
FEEDBACK_MIX     = {             # proportions must sum to 1.0
    "approve": 0.60,
    "reject":  0.25,
    "modify":  0.15,
}


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 – Generate synthetic data
# ─────────────────────────────────────────────────────────────────────────────

def generate_data(n_samples: int, n_features: int, n_classes: int, seed: int):
    """
    Generate a linearly-separable classification dataset with cluster structure.
    Returns (features: ndarray, labels: ndarray).
    """
    rng = np.random.RandomState(seed)
    samples_per_class = n_samples // n_classes
    remainder = n_samples - samples_per_class * n_classes

    X_parts, y_parts = [], []
    for cls in range(n_classes):
        n = samples_per_class + (1 if cls < remainder else 0)
        # Each class has a distinct cluster centre
        centre = rng.uniform(-3, 3, size=n_features) * (cls + 1)
        X_parts.append(rng.randn(n, n_features) * 0.8 + centre)
        y_parts.append(np.full(n, cls, dtype=int))

    X = np.vstack(X_parts)
    y = np.concatenate(y_parts)

    # Shuffle
    idx = rng.permutation(n_samples)
    return X[idx], y[idx]


def inject_noise(labels: np.ndarray, noise_rate: float, n_classes: int, seed: int):
    """
    Randomly flip `noise_rate` fraction of labels to a different class.
    Returns (noisy_labels, noisy_indices).
    """
    rng = np.random.RandomState(seed + 1)
    n_noisy = int(len(labels) * noise_rate)
    noisy_idx = rng.choice(len(labels), size=n_noisy, replace=False)

    noisy_labels = labels.copy()
    for i in noisy_idx:
        original = labels[i]
        choices = [c for c in range(n_classes) if c != original]
        noisy_labels[i] = rng.choice(choices)

    return noisy_labels, set(noisy_idx.tolist())


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _pct(a, b):
    return f"{a/b*100:.1f}%" if b else "0%"


def _print_section(title: str):
    logger.info("─" * 55)
    logger.info(f"  {title}")
    logger.info("─" * 55)


# ─────────────────────────────────────────────────────────────────────────────
# Main seeding logic
# ─────────────────────────────────────────────────────────────────────────────

def seed(demo_name: str, reset: bool):
    db = SessionLocal()
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    try:
        # ── Reset ──────────────────────────────────────────────────────────
        if reset:
            _print_section("Resetting existing demo data")
            existing = db.query(Dataset).filter(Dataset.name == demo_name).first()
            if existing:
                dataset_id = existing.id

                # Delete in FK order
                sample_ids = [
                    s.id for s in db.query(Sample.id)
                    .filter(Sample.dataset_id == dataset_id).all()
                ]
                if sample_ids:
                    detection_ids = [
                        d.id for d in db.query(Detection.id)
                        .filter(Detection.sample_id.in_(sample_ids)).all()
                    ]
                    if detection_ids:
                        suggestion_ids = [
                            s.id for s in db.query(Suggestion.id)
                            .filter(Suggestion.detection_id.in_(detection_ids)).all()
                        ]
                        if suggestion_ids:
                            db.query(Feedback).filter(
                                Feedback.suggestion_id.in_(suggestion_ids)
                            ).delete(synchronize_session=False)
                            db.query(Suggestion).filter(
                                Suggestion.id.in_(suggestion_ids)
                            ).delete(synchronize_session=False)
                        db.query(Detection).filter(
                            Detection.id.in_(detection_ids)
                        ).delete(synchronize_session=False)
                    db.query(Feedback).filter(
                        Feedback.sample_id.in_(sample_ids)
                    ).delete(synchronize_session=False)
                    db.query(Sample).filter(
                        Sample.dataset_id == dataset_id
                    ).delete(synchronize_session=False)

                db.query(MLModel).filter(
                    MLModel.dataset_id == dataset_id
                ).delete(synchronize_session=False)
                db.delete(existing)
                db.commit()
                logger.info(f"Deleted existing demo dataset (id={dataset_id})")
            else:
                logger.info("No existing demo dataset found — nothing to reset")

        # ── Check for duplicate name ───────────────────────────────────────
        if db.query(Dataset).filter(Dataset.name == demo_name).first():
            logger.error(
                f"Dataset '{demo_name}' already exists. "
                "Run with --reset to delete it first."
            )
            sys.exit(1)

        # ── Step 1: Generate data ──────────────────────────────────────────
        _print_section("Step 1 / 6 — Generating synthetic data")
        X, y_clean = generate_data(N_SAMPLES, N_FEATURES, N_CLASSES, RANDOM_SEED)
        y_noisy, noisy_indices = inject_noise(y_clean, NOISE_RATE, N_CLASSES, RANDOM_SEED)

        n_noisy = len(noisy_indices)
        logger.info(f"Generated {N_SAMPLES} samples × {N_FEATURES} features × {N_CLASSES} classes")
        logger.info(f"Injected noise: {n_noisy} samples ({_pct(n_noisy, N_SAMPLES)})")
        logger.info(f"Class distribution: { {c: int((y_noisy==c).sum()) for c in range(N_CLASSES)} }")

        # ── Step 2: Insert Dataset + Samples ──────────────────────────────
        _print_section("Step 2 / 6 — Inserting dataset and samples into DB")

        feature_names = [f"feature_{i+1}" for i in range(N_FEATURES)]

        dataset = Dataset(
            name=demo_name,
            description=(
                f"Auto-generated demo dataset. "
                f"{N_SAMPLES} samples, {N_FEATURES} features, {N_CLASSES} classes, "
                f"{int(NOISE_RATE*100)}% label noise injected."
            ),
            file_path=f"demo/{demo_name.lower().replace(' ', '_')}.csv",
            num_samples=N_SAMPLES,
            num_features=N_FEATURES,
            num_classes=N_CLASSES,
            feature_names=json.dumps(feature_names),
            label_column_name="label",
            is_active=True,
        )
        db.add(dataset)
        db.flush()  # get dataset.id without full commit
        dataset_id = dataset.id
        logger.info(f"Created dataset id={dataset_id}")

        samples = []
        for i in range(N_SAMPLES):
            s = Sample(
                dataset_id=dataset_id,
                sample_index=i,
                features=json.dumps([round(float(v), 6) for v in X[i]]),
                original_label=int(y_clean[i]),
                current_label=int(y_noisy[i]),
                is_suspicious=False,
                is_corrected=False,
            )
            db.add(s)
            samples.append(s)

        db.commit()
        # Refresh to get IDs
        for s in samples:
            db.refresh(s)

        logger.info(f"Inserted {len(samples)} samples")

        # ── Step 3: Run detection via ML engine ───────────────────────────
        _print_section("Step 3 / 6 — Running detection (ML engine)")

        from services.ml_integration import fit_dataset, detect_noise

        fit_result = fit_dataset(db, dataset_id)
        logger.info(
            f"Engine fitted: {fit_result['samples_fitted']} samples, "
            f"classes={fit_result['classes']}, threshold={fit_result.get('initial_threshold', '?')}"
        )

        detection_result = detect_noise(db, dataset_id)
        flagged = detection_result["flagged_samples"]
        threshold = detection_result["current_threshold"]
        logger.info(f"Detection: {len(flagged)} flagged at threshold={threshold:.3f}")

        # Insert Detection rows
        detections = []
        for f in flagged:
            sample = next((s for s in samples if s.id == f["sample_id"]), None)
            if not sample:
                continue

            noise_prob = float(f["noise_probability"])
            conf  = float(np.clip(noise_prob * 1.05, 0, 1))
            anom  = float(np.clip(noise_prob * 0.95, 0, 1))
            w_conf, w_anom = 0.6, 0.4
            weighted = conf * w_conf + anom * w_anom
            bonus    = conf * anom * 0.2
            priority = float(np.clip(weighted + bonus, 0, 1))

            dominant = "both" if conf >= 0.7 and anom >= 0.7 else (
                "confidence" if conf >= anom else "anomaly"
            )

            breakdown = {
                "noise_probability": round(noise_prob, 4),
                "confidence_score": round(conf, 4),
                "anomaly_score": round(anom, 4),
                "predicted_label": f["predicted_label"],
                "threshold": round(threshold, 4),
                "dominant_signal": dominant,
                "label_mismatch": int(f["predicted_label"]) != int(sample.current_label),
                "agreement_bonus": round(bonus, 4),
                "priority_breakdown": {
                    "weighted": round(weighted, 4),
                    "bonus": round(bonus, 4),
                    "final": round(priority, 4),
                },
            }

            det = Detection(
                sample_id=sample.id,
                iteration=1,
                confidence_score=conf,
                anomaly_score=anom,
                predicted_label=int(f["predicted_label"]),
                priority_score=priority,
                signal_breakdown=json.dumps(breakdown),
                priority_weights=json.dumps({"confidence": w_conf, "anomaly": w_anom}),
            )
            db.add(det)
            sample.is_suspicious = True
            detections.append((det, sample))

        db.commit()
        for det, _ in detections:
            db.refresh(det)

        logger.info(f"Inserted {len(detections)} detection records")

        if not detections:
            logger.warning(
                "Engine flagged 0 samples. "
                "The demo will still work but feedback/correction steps will be skipped."
            )
            _finish(dataset_id)
            return

        # ── Step 4: Generate suggestions ──────────────────────────────────
        _print_section("Step 4 / 6 — Generating suggestions")

        suggestions_created = []
        for det, sample in detections:
            predicted = det.predicted_label
            reason = (
                f"Model predicts class {predicted} but current label is "
                f"{sample.current_label} (confidence={det.confidence_score:.2f})"
            )
            sug = Suggestion(
                detection_id=det.id,
                suggested_label=predicted,
                reason=reason,
                confidence=det.confidence_score,
                status="pending",
            )
            db.add(sug)
            suggestions_created.append((sug, det, sample))

        db.commit()
        for sug, _, _ in suggestions_created:
            db.refresh(sug)

        logger.info(f"Created {len(suggestions_created)} suggestions")

        # ── Step 5: Simulate feedback ──────────────────────────────────────
        _print_section("Step 5 / 6 — Simulating feedback")

        # Pick up to N_FEEDBACK suggestions to review
        pool = suggestions_created[:N_FEEDBACK]
        n_approve = int(N_FEEDBACK * FEEDBACK_MIX["approve"])
        n_reject  = int(N_FEEDBACK * FEEDBACK_MIX["reject"])
        n_modify  = N_FEEDBACK - n_approve - n_reject  # remainder

        actions = (
            ["approve"] * n_approve +
            ["reject"]  * n_reject  +
            ["modify"]  * n_modify
        )
        random.shuffle(actions)

        feedback_records = []
        for (sug, det, sample), action in zip(pool, actions):
            if action == "approve":
                final_label = sug.suggested_label
                sug.status = "accepted"
            elif action == "reject":
                final_label = sample.current_label  # keep original
                sug.status = "rejected"
            else:  # modify
                # pick a different label from the suggested one
                other = [c for c in range(N_CLASSES) if c != sug.suggested_label]
                final_label = random.choice(other)
                sug.status = "modified"

            sug.reviewed_at = datetime.now(timezone.utc)
            sug.reviewer_notes = f"Demo seed — {action}"

            fb = Feedback(
                suggestion_id=sug.id,
                sample_id=sample.id,
                action=action,
                final_label=final_label,
                iteration=1,
                review_time_seconds=round(random.uniform(3.0, 45.0), 1),
            )
            db.add(fb)
            feedback_records.append((fb, sample, final_label, action))

        db.commit()

        counts = {a: sum(1 for _, _, _, act in feedback_records if act == a)
                  for a in ("approve", "reject", "modify")}
        logger.info(
            f"Simulated {len(feedback_records)} feedback records — "
            f"approve={counts['approve']}, reject={counts['reject']}, modify={counts['modify']}"
        )

        # ── Step 6: Apply corrections ──────────────────────────────────────
        _print_section("Step 6 / 6 — Applying corrections & retraining")

        corrections_applied = 0
        for fb, sample, final_label, action in feedback_records:
            if action in ("approve", "modify"):
                sample.current_label = final_label
                sample.is_corrected = True
                corrections_applied += 1

        db.commit()
        logger.info(f"Applied {corrections_applied} label corrections")

        # Retrain engine
        try:
            from services.ml_integration import run_learning_cycle
            cycle_result = run_learning_cycle(dataset_id)
            logger.info(
                f"Learning cycle complete — "
                f"meta_trained={cycle_result['meta_model']['trained']}, "
                f"threshold={cycle_result['threshold']['new_threshold']:.3f}, "
                f"retrained={cycle_result['retrain']['retrained']}"
            )
        except Exception as e:
            logger.warning(f"Learning cycle skipped (needs more feedback): {e}")

        _finish(dataset_id)

    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


def _finish(dataset_id: int):
    _print_section("Demo seed complete")
    logger.info(f"Dataset ID : {dataset_id}")
    logger.info(f"Name       : {DEMO_NAME}")
    logger.info(f"Samples    : {N_SAMPLES}  ({int(NOISE_RATE*100)}% noise injected)")
    logger.info(f"Features   : {N_FEATURES}")
    logger.info(f"Classes    : {N_CLASSES}")
    logger.info("")
    logger.info("Next steps:")
    logger.info(f"  1. Open the app → select dataset id={dataset_id}")
    logger.info(f"  2. Go to Detection → run detection")
    logger.info(f"  3. Go to Correction → review suggestions")
    logger.info(f"  4. Go to Evaluation → see accuracy improvement")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed SLDCE with a demo dataset for presentations."
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Delete existing demo dataset before seeding"
    )
    parser.add_argument(
        "--name", default=DEMO_NAME,
        help=f"Dataset name (default: '{DEMO_NAME}')"
    )
    args = parser.parse_args()

    seed(demo_name=args.name, reset=args.reset)