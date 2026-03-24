"""
Day 6: SLDCE Failure Case Analysis
Answers:
  1. What samples did SLDCE MISS? (false negatives — noisy but not corrected)
  2. What samples did SLDCE WRONGLY FLAG? (false positives — clean but flagged)

Usage:
    cd backend
    python benchmarks/failure_analysis.py --dataset_id 11
"""
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import confusion_matrix

from core.database import SessionLocal
from models.dataset import Sample


def analyze(dataset_id: int):
    db = SessionLocal()

    samples = (
        db.query(Sample)
        .filter(Sample.dataset_id == dataset_id)
        .order_by(Sample.sample_index)
        .all()
    )
    db.close()

    if not samples:
        print("No samples found.")
        return

    # Build arrays
    X, y_original, y_current, sample_ids, is_corrected, is_suspicious = [], [], [], [], [], []
    for s in samples:
        feat = json.loads(s.features)
        X.append(feat if isinstance(feat, list) else list(feat.values()))
        y_original.append(s.original_label)
        y_current.append(s.current_label)
        sample_ids.append(s.id)
        is_corrected.append(bool(s.is_corrected))
        is_suspicious.append(bool(s.is_suspicious))

    X = np.array(X)
    y_original = np.array(y_original)
    y_current = np.array(y_current)
    is_corrected = np.array(is_corrected)
    is_suspicious = np.array(is_suspicious)

    n = len(samples)

    # Ground truth: which samples were originally noisy
    # A sample was noisy if original_label != current_label (SLDCE changed it)
    # OR if original_label != model_prediction and it was suspicious
    # We use: noisy_gt = samples where original != current (SLDCE corrected them)
    # + samples where original != current_label that were NOT corrected (missed)

    # Since we don't have true ground truth labels post-correction,
    # we use the model's out-of-fold predictions as proxy ground truth
    classes = np.unique(y_current)
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    skf = StratifiedKFold(n_splits=min(5, len(classes)), shuffle=True, random_state=42)
    pred_probs = cross_val_predict(clf, X, y_current, cv=skf, method="predict_proba")
    model_predictions = classes[np.argmax(pred_probs, axis=1)]

    # Noise score per sample
    noise_scores = np.array([
        1.0 - pred_probs[i, list(classes).index(y_current[i])]
        for i in range(n)
    ])

    # Define: a sample is "truly noisy" if model strongly disagrees with original label
    # Using original labels to detect what was noisy before correction
    clf2 = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    skf2 = StratifiedKFold(n_splits=min(5, len(classes)), shuffle=True, random_state=42)
    pred_probs_orig = cross_val_predict(clf2, X, y_original, cv=skf2, method="predict_proba")
    model_pred_orig = classes[np.argmax(pred_probs_orig, axis=1)]

    noise_score_orig = np.array([
        1.0 - pred_probs_orig[i, list(classes).index(y_original[i])]
        for i in range(n)
    ])

    # Ground truth noisy: model strongly disagrees with original label (noise_score > 0.5)
    # AND model prediction != original label
    truly_noisy = (noise_score_orig > 0.5) & (model_pred_orig != y_original)
    sldce_flagged = is_suspicious  # flagged by SLDCE at any point

    # Confusion matrix of SLDCE detection
    tp = np.sum(truly_noisy & sldce_flagged)   # correctly flagged noisy
    fp = np.sum(~truly_noisy & sldce_flagged)  # wrongly flagged clean
    fn = np.sum(truly_noisy & ~sldce_flagged)  # missed noisy samples
    tn = np.sum(~truly_noisy & ~sldce_flagged) # correctly ignored clean

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print("\n" + "="*60)
    print("  SLDCE FAILURE CASE ANALYSIS")
    print("="*60)
    print(f"\n  Dataset ID: {dataset_id}")
    print(f"  Total samples: {n}")
    print(f"  Truly noisy (estimated): {truly_noisy.sum()}")
    print(f"  SLDCE flagged: {sldce_flagged.sum()}")
    print(f"  SLDCE corrected: {is_corrected.sum()}")

    print(f"\n  Detection Performance:")
    print(f"  {'True Positives (correctly flagged):':<40} {tp}")
    print(f"  {'False Positives (wrongly flagged):':<40} {fp}")
    print(f"  {'False Negatives (missed noisy):':<40} {fn}")
    print(f"  {'True Negatives (correctly ignored):':<40} {tn}")
    print(f"\n  Precision: {precision:.4f} ({precision*100:.2f}%)")
    print(f"  Recall:    {recall:.4f} ({recall*100:.2f}%)")
    print(f"  F1 Score:  {f1:.4f} ({f1*100:.2f}%)")

    # False negatives — missed noisy samples
    fn_indices = np.where(truly_noisy & ~sldce_flagged)[0]
    print(f"\n{'─'*60}")
    print(f"  FALSE NEGATIVES — {len(fn_indices)} samples SLDCE MISSED")
    print(f"{'─'*60}")
    if len(fn_indices) == 0:
        print("  None! SLDCE caught all noisy samples.")
    else:
        print(f"  {'ID':<8} {'Original':<10} {'Model Pred':<12} {'Noise Score':<14} {'Features'}")
        print(f"  {'─'*6:<8} {'─'*8:<10} {'─'*10:<12} {'─'*11:<14}")
        for idx in fn_indices[:20]:  # show max 20
            s = samples[idx]
            feat = json.loads(s.features)
            feat_vals = feat if isinstance(feat, list) else list(feat.values())
            print(
                f"  {s.id:<8} {y_original[idx]:<10} {model_pred_orig[idx]:<12} "
                f"{noise_score_orig[idx]:.3f}{'':9} {[round(v,2) for v in feat_vals[:3]]}..."
            )
        if len(fn_indices) > 20:
            print(f"  ... and {len(fn_indices)-20} more")

    # False positives — wrongly flagged clean samples
    fp_indices = np.where(~truly_noisy & sldce_flagged)[0]
    print(f"\n{'─'*60}")
    print(f"  FALSE POSITIVES — {len(fp_indices)} CLEAN samples WRONGLY FLAGGED")
    print(f"{'─'*60}")
    if len(fp_indices) == 0:
        print("  None! SLDCE didn't wrongly flag any clean samples.")
    else:
        print(f"  {'ID':<8} {'Label':<10} {'Model Pred':<12} {'Noise Score':<14} {'Features'}")
        print(f"  {'─'*6:<8} {'─'*8:<10} {'─'*10:<12} {'─'*11:<14}")
        for idx in fp_indices[:20]:
            s = samples[idx]
            feat = json.loads(s.features)
            feat_vals = feat if isinstance(feat, list) else list(feat.values())
            print(
                f"  {s.id:<8} {y_original[idx]:<10} {model_pred_orig[idx]:<12} "
                f"{noise_score_orig[idx]:.3f}{'':9} {[round(v,2) for v in feat_vals[:3]]}..."
            )
        if len(fp_indices) > 20:
            print(f"  ... and {len(fp_indices)-20} more")

    # Class-level breakdown
    print(f"\n{'─'*60}")
    print(f"  CLASS-LEVEL FAILURE BREAKDOWN")
    print(f"{'─'*60}")
    print(f"  {'Class':<8} {'Noisy':<8} {'Missed':<8} {'Wrong Flag':<12} {'Miss Rate'}")
    for c in sorted(classes):
        class_noisy = np.sum(truly_noisy & (y_original == c))
        class_missed = np.sum(truly_noisy & ~sldce_flagged & (y_original == c))
        class_wrong = np.sum(~truly_noisy & sldce_flagged & (y_original == c))
        miss_rate = class_missed / class_noisy if class_noisy > 0 else 0
        print(f"  {c:<8} {class_noisy:<8} {class_missed:<8} {class_wrong:<12} {miss_rate*100:.1f}%")

    # Summary insight
    print(f"\n{'─'*60}")
    print(f"  KEY INSIGHTS")
    print(f"{'─'*60}")
    if fn == 0:
        print(f"  ✅ SLDCE missed zero noisy samples (perfect recall)")
    else:
        print(f"  ⚠️  SLDCE missed {fn} noisy samples ({fn/truly_noisy.sum()*100:.1f}% miss rate)")
        print(f"     These tend to have lower noise scores (harder to detect)")

    if fp == 0:
        print(f"  ✅ SLDCE had zero false positives (perfect precision)")
    else:
        print(f"  ⚠️  SLDCE wrongly flagged {fp} clean samples")
        if len(fp_indices) > 0:
            avg_fp_noise = noise_score_orig[fp_indices].mean()
            print(f"     Average noise score of wrongly flagged: {avg_fp_noise:.3f}")
            print(f"     These are likely borderline/ambiguous samples near class boundaries")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_id", type=int, required=True)
    args = parser.parse_args()
    analyze(args.dataset_id)