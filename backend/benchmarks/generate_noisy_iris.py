"""
Generates a fresh Iris dataset with exactly 15% label noise.
Run this once to create the canonical benchmark dataset.

Usage:
    cd backend
    python benchmarks/generate_noisy_iris.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from sklearn.datasets import load_iris

# Fixed seed for reproducibility
RANDOM_STATE = 42
NOISE_RATE = 0.15

iris = load_iris()
X = iris.data
y = iris.target.copy()
feature_names = iris.feature_names
n_samples = len(y)
n_classes = len(np.unique(y))

# Inject noise
rng = np.random.RandomState(RANDOM_STATE)
n_noisy = int(n_samples * NOISE_RATE)
noisy_indices = rng.choice(n_samples, size=n_noisy, replace=False)

for idx in noisy_indices:
    original = y[idx]
    other_classes = [c for c in range(n_classes) if c != original]
    y[idx] = rng.choice(other_classes)

# Build DataFrame
df = pd.DataFrame(X, columns=feature_names)
df['class'] = y

# Save
output_path = Path(__file__).parent / "iris_noisy_15pct.csv"
df.to_csv(output_path, index=False)

# Report
n_changed = (y != iris.target).sum()
print(f"Dataset: {n_samples} samples, {n_classes} classes")
print(f"Noise injected: {n_changed} samples ({n_changed/n_samples:.1%})")
print(f"Saved to: {output_path}")