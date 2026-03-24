"""
meta_model.py
-------------
Trains a LogisticRegression meta-model to learn:
    signal_vector → P(label_is_noisy)

The meta-model is a second-level learner that uses reviewer feedback
(approved corrections = noisy label, rejected corrections = clean label)
as training signal to become progressively better at detecting noise.

Key design decisions:
  - Uses incremental feedback storage (lists) that grow over time.
  - Only trains when both classes (noisy=1, clean=0) are present.
  - StandardScaler normalizes signals before training.
  - predict_proba returns P(noise=1) which feeds the decision controller.

Connects to: signal_vector.py (input features), feedback.py (training labels),
             decision.py (consumes noise probability).
"""

import numpy as np
from typing import List, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


class MetaNoiseModel:
    """
    Learns to predict label noise probability from signal vectors.

    The model accumulates (signal_vector, is_noisy) pairs from human feedback
    and retrains a LogisticRegression classifier when enough diverse examples
    are available.

    Parameters
    ----------
    random_state : int
        Seed for LogisticRegression. Default: 42.
    min_samples_to_train : int
        Minimum number of feedback samples required before training.
        Default: 10. Prevents training on trivially small datasets.
    """

    def __init__(self, random_state: int = 42, min_samples_to_train: int = 10) -> None:
        self.random_state = random_state
        self.min_samples_to_train = min_samples_to_train

        self.classifier = LogisticRegression(
            max_iter=1000,
            random_state=random_state,
            solver="lbfgs",
        )
        self.scaler = StandardScaler()

        # Accumulated feedback data
        self._X_feedback: List[np.ndarray] = []
        self._y_feedback: List[int] = []  # 1 = noisy, 0 = clean

        self._fitted = False

    def add_feedback(self, signal_vector: np.ndarray, is_noisy: bool) -> None:
        """
        Store a labeled example from human feedback.

        Parameters
        ----------
        signal_vector : np.ndarray
            Feature vector produced by SignalVectorBuilder.
        is_noisy : bool
            True if reviewer confirmed the label was noisy (correction approved).
            False if reviewer rejected the correction (label was clean).
        """
        self._X_feedback.append(signal_vector.copy())
        self._y_feedback.append(int(is_noisy))

    def train(self) -> bool:
        """
        (Re)train the meta-model on all accumulated feedback.

        Returns
        -------
        bool
            True if training was performed, False if skipped.
        """
        n = len(self._y_feedback)
        if n < self.min_samples_to_train:
            return False

        y_arr = np.array(self._y_feedback)
        unique_classes = np.unique(y_arr)
        if len(unique_classes) < 2:
            # Cannot train binary classifier with only one class present.
            # This can happen early in the feedback cycle.
            return False

        X_arr = np.vstack(self._X_feedback)
        X_scaled = self.scaler.fit_transform(X_arr)
        self.classifier.fit(X_scaled, y_arr)
        self._fitted = True
        return True

    def predict_noise_probabilities(self, signal_matrix: np.ndarray) -> np.ndarray:
        if not self._fitted:
            # Use weighted heuristic from raw signals instead of flat 0.5
            # Signals layout: [max_confidence, entropy, margin, disagreement, ...]
            if signal_matrix.shape[1] >= 4:
                entropy      = signal_matrix[:, 1].astype(float)
                margin       = signal_matrix[:, 2].astype(float)
                disagreement = signal_matrix[:, 3].astype(float)

                def norm(x: np.ndarray) -> np.ndarray:
                    r = x.max() - x.min()
                    return (x - x.min()) / r if r > 1e-8 else np.full_like(x, 0.5)

                score = (norm(entropy) + (1.0 - norm(margin)) + norm(disagreement)) / 3.0
                return np.clip(score, 0.0, 1.0)
            return np.full(signal_matrix.shape[0], 0.5)

        X_scaled = self.scaler.transform(signal_matrix)
        proba = self.classifier.predict_proba(X_scaled)
        classes = list(self.classifier.classes_)
        noisy_idx = classes.index(1)
        return proba[:, noisy_idx]

    def predict_noise_probability(self, signal_vector: np.ndarray) -> float:
        if not self._fitted:
            if len(signal_vector) >= 4:
                entropy      = float(signal_vector[1])
                margin       = float(signal_vector[2])
                disagreement = float(signal_vector[3])
                score = (entropy + (1.0 - margin) + disagreement) / 3.0
                return float(np.clip(score, 0.0, 1.0))
            return 0.5

        X_scaled = self.scaler.transform(signal_vector.reshape(1, -1))
        proba = self.classifier.predict_proba(X_scaled)[0]
        classes = list(self.classifier.classes_)
        noisy_idx = classes.index(1)
        return float(proba[noisy_idx])

    def feedback_count(self) -> int:
        """Return total number of feedback examples accumulated."""
        return len(self._y_feedback)

    def is_trained(self) -> bool:
        """Return True if the meta-model has been fitted at least once."""
        return self._fitted
