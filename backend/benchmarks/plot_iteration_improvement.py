# backend/benchmarks/plot_iteration_improvement.py
"""
Day 3: Generate iteration improvement plot.
Reads from DB and saves benchmarks/iteration_improvement.png

Usage:
    cd backend
    python benchmarks/plot_iteration_improvement.py --dataset_id 11
"""
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from core.database import SessionLocal
from services.benchmark_service import get_benchmark_results


def plot(dataset_id: int):
    db = SessionLocal()
    try:
        results = get_benchmark_results(db, dataset_id)
    finally:
        db.close()

    if not results:
        print("No benchmark results found. Run benchmarks first.")
        return

    # --- Extract data ---
    # SLDCE iterations
    sldce = sorted(
        [r for r in results if r['tool'] == 'sldce'],
        key=lambda x: x['iteration']
    )
    # Keep only latest run per iteration (in case of duplicates)
    seen = {}
    for r in sldce:
        seen[r['iteration']] = r
    sldce = [seen[k] for k in sorted(seen.keys())]

    sldce_iters = [r['iteration'] for r in sldce]
    sldce_acc   = [r['accuracy'] * 100 for r in sldce]
    sldce_prec  = [r['precision'] * 100 for r in sldce]
    sldce_rec   = [r['recall'] * 100 for r in sldce]
    sldce_effort = [r['human_effort'] or 0 for r in sldce]

    # Baselines (latest run per tool)
    def latest(tool):
        rows = [r for r in results if r['tool'] == tool]
        return rows[-1] if rows else None

    no_corr  = latest('no_correction')
    random   = latest('random')
    cleanlab = latest('cleanlab')

    # --- Figure ---
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(
        f'SLDCE Iterative Improvement — Dataset {dataset_id}',
        fontsize=14, fontweight='bold', y=1.02
    )

    SLDCE_COLOR    = '#2ecc71'
    CLEANLAB_COLOR = '#3498db'
    RANDOM_COLOR   = '#f39c12'
    NOCORR_COLOR   = '#e74c3c'

    # ── Plot 1: Accuracy over iterations ──────────────────────────────
    ax1 = axes[0]
    ax1.plot(sldce_iters, sldce_acc, 'o-',
             color=SLDCE_COLOR, linewidth=2.5, markersize=8,
             label='SLDCE', zorder=5)

    # Baseline horizontal lines
    if no_corr:
        ax1.axhline(no_corr['accuracy'] * 100, color=NOCORR_COLOR,
                    linestyle='--', linewidth=1.5, label='No Correction')
    if random:
        ax1.axhline(random['accuracy'] * 100, color=RANDOM_COLOR,
                    linestyle='--', linewidth=1.5, label='Random')
    if cleanlab:
        ax1.axhline(cleanlab['accuracy'] * 100, color=CLEANLAB_COLOR,
                    linestyle='--', linewidth=1.5, label='Cleanlab')

    # Annotate each point
    for i, (x, y) in enumerate(zip(sldce_iters, sldce_acc)):
        ax1.annotate(f'{y:.1f}%', (x, y),
                     textcoords='offset points', xytext=(0, 10),
                     ha='center', fontsize=8, color=SLDCE_COLOR, fontweight='bold')

    ax1.set_xlabel('Iteration', fontsize=11)
    ax1.set_ylabel('Accuracy (%)', fontsize=11)
    ax1.set_title('Accuracy per Iteration', fontsize=12, fontweight='bold')
    ax1.set_xticks(sldce_iters)
    ax1.set_ylim(
        max(0, min(sldce_acc + [no_corr['accuracy']*100 if no_corr else 100]) - 10),
        105
    )
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # ── Plot 2: Precision & Recall over iterations ────────────────────
    ax2 = axes[1]
    ax2.plot(sldce_iters, sldce_prec, 's-',
             color='#9b59b6', linewidth=2, markersize=7, label='Precision')
    ax2.plot(sldce_iters, sldce_rec, '^-',
             color='#1abc9c', linewidth=2, markersize=7, label='Recall')

    ax2.set_xlabel('Iteration', fontsize=11)
    ax2.set_ylabel('Score (%)', fontsize=11)
    ax2.set_title('Precision & Recall per Iteration', fontsize=12, fontweight='bold')
    ax2.set_xticks(sldce_iters)
    ax2.set_ylim(
        max(0, min(sldce_prec + sldce_rec) - 10),
        105
    )
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    # ── Plot 3: Human effort over iterations ─────────────────────────
    ax3 = axes[2]
    bars = ax3.bar(sldce_iters, sldce_effort,
                   color=SLDCE_COLOR, alpha=0.8, edgecolor='white', linewidth=1.5)

    # Annotate bars
    for bar, val in zip(bars, sldce_effort):
        ax3.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.5,
                 str(val), ha='center', va='bottom',
                 fontsize=9, fontweight='bold')

    ax3.set_xlabel('Iteration', fontsize=11)
    ax3.set_ylabel('Samples Reviewed', fontsize=11)
    ax3.set_title('Human Effort per Iteration', fontsize=12, fontweight='bold')
    ax3.set_xticks(sldce_iters)
    ax3.grid(True, alpha=0.3, axis='y')

    # ── Summary text box ─────────────────────────────────────────────
    if no_corr and sldce_acc:
        improvement = sldce_acc[-1] - no_corr['accuracy'] * 100
        total_effort = sum(sldce_effort)
        summary = (
            f"Start accuracy: {no_corr['accuracy']*100:.1f}%\n"
            f"Final accuracy: {sldce_acc[-1]:.1f}%\n"
            f"Improvement: +{improvement:.1f}%\n"
            f"Total samples reviewed: {total_effort}"
        )
        fig.text(0.5, -0.04, summary,
                 ha='center', fontsize=10,
                 bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.8))

    plt.tight_layout()

    # Save
    output_path = Path(__file__).parent / "iteration_improvement.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

    print(f"Plot saved to: {output_path}")
    print(f"\nSLDCE Results Summary:")
    print(f"{'Iter':<6} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'Effort'}")
    print("-" * 54)
    for r in sldce:
        print(
            f"{r['iteration']:<6} "
            f"{r['accuracy']*100:<12.2f} "
            f"{r['precision']*100:<12.2f} "
            f"{r['recall']*100:<12.2f} "
            f"{r['human_effort'] or 0}"
        )
    if no_corr:
        print(f"\nBaseline (no correction): {no_corr['accuracy']*100:.2f}%")
    if cleanlab:
        print(f"Cleanlab:                 {cleanlab['accuracy']*100:.2f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_id", type=int, required=True)
    args = parser.parse_args()
    plot(args.dataset_id)