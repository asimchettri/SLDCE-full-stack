"""
Day 1 Cleanlab benchmark runner.
Run this script directly to generate benchmarks/cleanlab_dataset1.csv

Usage:
    cd backend
    python benchmarks/run_cleanlab_day1.py --dataset_id 1
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from core.database import SessionLocal


def get_X_y(db, dataset_id: int):
    """Load dataset samples as numpy arrays."""
    import json
    from models.dataset import Sample

    samples = (
        db.query(Sample)
        .filter(Sample.dataset_id == dataset_id)
        .order_by(Sample.sample_index)
        .all()
    )

    if not samples:
        print(f"ERROR: No samples found for dataset {dataset_id}")
        sys.exit(1)

    X_rows, y_rows = [], []
    for s in samples:
        features = json.loads(s.features)
        X_rows.append(features if isinstance(features, list) else list(features.values()))
        y_rows.append(s.current_label)

    return np.array(X_rows, dtype=float), np.array(y_rows, dtype=int)


def run(dataset_id: int):
    print(f"\n{'='*60}")
    print(f"  CLEANLAB DAY 1 BENCHMARK — Dataset {dataset_id}")
    print(f"{'='*60}\n")

    db = SessionLocal()

    try:
        from models.dataset import Dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            print(f"ERROR: Dataset {dataset_id} not found")
            sys.exit(1)

        print(f"Dataset: {dataset.name}")
        print(f"Samples: {dataset.num_samples}")
        print(f"Features: {dataset.num_features}")
        print(f"Classes: {dataset.num_classes}\n")

        # Load data
        X, y = get_X_y(db, dataset_id)
        print(f"Loaded X: {X.shape}, y: {y.shape}")
        print(f"Classes found: {np.unique(y)}\n")

        # Step 1: Baseline (no correction)
        print("Step 1: Computing baseline accuracy (no correction)...")
        clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        n_splits = min(5, len(np.unique(y)))
        y_pred_base = cross_val_predict(clf, X, y, cv=n_splits)
        baseline_acc = accuracy_score(y, y_pred_base)
        print(f"  Baseline accuracy: {baseline_acc:.4f}\n")

        # Step 2: Get predicted probabilities for Cleanlab
        print("Step 2: Computing out-of-fold predicted probabilities...")
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        pred_probs = cross_val_predict(
            clf, X, y, cv=skf, method="predict_proba"
        )
        print(f"  pred_probs shape: {pred_probs.shape}\n")

        # Step 3: Run Cleanlab
        print("Step 3: Running Cleanlab find_label_issues...")
        try:
            from cleanlab.filter import find_label_issues
        except ImportError:
            print("ERROR: cleanlab not installed. Run: pip install cleanlab")
            sys.exit(1)

        issue_indices = find_label_issues(
            labels=y,
            pred_probs=pred_probs,
            return_indices_ranked_by="self_confidence",
        )
        num_issues = len(issue_indices)
        issue_rate = num_issues / len(y)

        print(f"  Issues found: {num_issues} / {len(y)}")
        print(f"  Issue rate: {issue_rate:.2%}\n")

        # Step 4: Score after removing flagged samples
        print("Step 4: Scoring after Cleanlab cleaning...")
        mask = np.ones(len(y), dtype=bool)
        mask[issue_indices] = False
        X_clean, y_clean = X[mask], y[mask]

        y_pred_clean = cross_val_predict(
            clf, X_clean, y_clean, cv=min(5, len(np.unique(y_clean)))
        )
        clean_acc = accuracy_score(y_clean, y_pred_clean)
        clean_prec = precision_score(y_clean, y_pred_clean, average="weighted", zero_division=0)
        clean_rec = recall_score(y_clean, y_pred_clean, average="weighted", zero_division=0)
        clean_f1 = f1_score(y_clean, y_pred_clean, average="weighted", zero_division=0)

        print(f"  Accuracy after cleaning:  {clean_acc:.4f}")
        print(f"  Precision after cleaning: {clean_prec:.4f}")
        print(f"  Recall after cleaning:    {clean_rec:.4f}")
        print(f"  F1 after cleaning:        {clean_f1:.4f}\n")

        # Step 5: Write CSV
        output_dir = Path(__file__).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = output_dir / "cleanlab_dataset1.csv"

        rows = [
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset.name,
                "tool": "no_correction",
                "num_samples": len(y),
                "num_issues_found": 0,
                "issue_rate": 0.0,
                "accuracy": round(baseline_acc, 4),
                "precision": None,
                "recall": None,
                "f1": None,
            },
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset.name,
                "tool": "cleanlab",
                "num_samples": int(mask.sum()),
                "num_issues_found": num_issues,
                "issue_rate": round(issue_rate, 4),
                "accuracy": round(clean_acc, 4),
                "precision": round(clean_prec, 4),
                "recall": round(clean_rec, 4),
                "f1": round(clean_f1, 4),
            },
        ]

        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        print(f"Results written to: {csv_path}")

        # Summary
        print(f"\n{'='*60}")
        print("  SUMMARY")
        print(f"{'='*60}")
        print(f"  Baseline accuracy:        {baseline_acc:.4f}")
        print(f"  Cleanlab accuracy:        {clean_acc:.4f}")
        print(f"  Improvement:              {clean_acc - baseline_acc:+.4f}")
        print(f"  Issues found:             {num_issues} ({issue_rate:.2%})")
        print(f"{'='*60}\n")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Cleanlab Day 1 benchmark")
    parser.add_argument(
        "--dataset_id", type=int, required=True,
        help="ID of the dataset to benchmark"
    )
    args = parser.parse_args()
    run(args.dataset_id)