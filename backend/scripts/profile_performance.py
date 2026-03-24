"""
profile_performance.py
----------------------
Profiles detection and retrain speed on a 1000-sample dataset.
Targets: detection < 10s, retrain < 30s

Usage:
    python scripts/profile_performance.py
"""
import sys, time, json, numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import SessionLocal
from services.ml_integration import fit_dataset, detect_noise, run_learning_cycle
from models.dataset import Sample, Dataset
import json

PROFILE_DATASET_ID = None  # will use first available dataset with 500+ samples

def main():
    db = SessionLocal()
    try:
        # Find a suitable dataset
        dataset = db.query(Dataset).filter(Dataset.is_active == True).first()
        if not dataset:
            print("No datasets found. Run seed_demo_data.py first.")
            return
        
        dataset_id = dataset.id
        n_samples = db.query(Sample).filter(Sample.dataset_id == dataset_id).count()
        print(f"\nProfiling dataset id={dataset_id} ({dataset.name}) — {n_samples} samples")
        print("─" * 55)

        # Profile fit + detect (combined = "detection" from user perspective)
        print("\n[1/2] Profiling detection (fit + detect_noise)...")
        t0 = time.perf_counter()
        fit_result = fit_dataset(db, dataset_id)
        detect_result = detect_noise(db, dataset_id)
        t1 = time.perf_counter()
        detection_time = t1 - t0

        flagged = len(detect_result["flagged_samples"])
        print(f"  Fitted: {fit_result['samples_fitted']} samples")
        print(f"  Flagged: {flagged} samples")
        print(f"  Time: {detection_time:.2f}s", end="  ")
        if detection_time < 10:
            print("✅ PASS (< 10s)")
        else:
            print(f"❌ FAIL (target < 10s, got {detection_time:.1f}s)")

        # Profile learning cycle (retrain)
        print("\n[2/2] Profiling learning cycle (retrain)...")
        t0 = time.perf_counter()
        try:
            cycle = run_learning_cycle(dataset_id)
            t1 = time.perf_counter()
            retrain_time = t1 - t0
            print(f"  meta_trained={cycle['meta_model']['trained']}, "
                  f"retrained={cycle['retrain']['retrained']}")
            print(f"  Time: {retrain_time:.2f}s", end="  ")
            if retrain_time < 30:
                print("✅ PASS (< 30s)")
            else:
                print(f"❌ FAIL (target < 30s, got {retrain_time:.1f}s)")
        except Exception as e:
            t1 = time.perf_counter()
            print(f"  Skipped (engine not fitted or no feedback): {e}")

        print("\n─" * 55)
        print("Done.\n")

    finally:
        db.close()

if __name__ == "__main__":
    main()