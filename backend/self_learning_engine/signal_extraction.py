"""
signal_extraction.py
--------------------
Computes per-sample noise detection signals from ensemble outputs
and anomaly detectors.

Each signal captures a distinct perspective on why a sample might be
mislabeled or anomalous:

  - max_confidence  : how certain is the ensemble of its best class?
  - entropy         : overall uncertainty across class distribution
  - margin          : gap between top-2 predictions (small margin = ambiguous)
  - disagreement    : how much do individual models disagree with each other?
  - isolation_score : global anomaly score (IsolationForest)
  - lof_score       : local density anomaly score (LocalOutlierFactor)
  - centroid_dist   : distance from sample to its predicted class centroid

Connects to: signal_vector.py (assembles signals into a numeric vector),
             ensemble.py (consumes model probabilities).
"""

import numpy as np
from typing import List, Dict
from scipy.stats import entropy as scipy_entropy
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import LabelEncoder


class SignalExtractor:
    """
    Computes noise detection signals for each sample.

    Parameters
    ----------
    contamination : float
        Expected fraction of anomalies used by IsolationForest and LOF.
        Should reflect domain knowledge or be kept conservatively small.
        Default: 0.1 (10% expected noise).
    n_neighbors_lof : int
        Number of neighbors for LocalOutlierFactor.
        Default: 20.
    random_state : int
        Seed for IsolationForest.
        Default: 42.
    """

    def __init__(
        self,
        contamination: float = 0.1,
        n_neighbors_lof: int = 20,
        random_state: int = 42,
    ) -> None:
        self.contamination = contamination
        self.n_neighbors_lof = n_neighbors_lof
        self.random_state = random_state

        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        self.lof = LocalOutlierFactor(
            n_neighbors=n_neighbors_lof,
            contamination=contamination,
            novelty=True,  # novelty=True to enable predict on new data
            n_jobs=1,
        )
        self._fitted = False

    def fit(self, X: np.ndarray) -> None:
        """
        Fit IsolationForest and LOF on training data.

        Parameters
        ----------
        X : np.ndarray
            Preprocessed feature matrix.
        """
        self.isolation_forest.fit(X)
        self.lof.fit(X)
        self._fitted = True

    def compute_signals(
        self,
        X: np.ndarray,
        y: np.ndarray,
        per_model_proba: List[np.ndarray],
        mean_proba: np.ndarray,
        classes: np.ndarray,
    ) -> List[Dict[str, float]]:
        """
        Compute noise signals for every sample.

        Parameters
        ----------
        X : np.ndarray
            Preprocessed features.
        y : np.ndarray
            Original labels.
        per_model_proba : List[np.ndarray]
            Probability matrices from each model.
        mean_proba : np.ndarray
            Averaged probability matrix (n_samples, n_classes).
        classes : np.ndarray
            Ordered class labels from the ensemble.

        Returns
        -------
        List[Dict[str, float]]
            One dict per sample with keys:
            max_confidence, entropy, margin, disagreement,
            isolation_score, lof_score, centroid_dist.
        """
        if not self._fitted:
            raise RuntimeError("SignalExtractor not fitted. Call fit() first.")

        n_samples = X.shape[0]
        label_enc = LabelEncoder()
        label_enc.classes_ = classes
        y_indices = np.array([np.where(classes == label)[0][0] for label in y])

        # --- Anomaly scores (higher = more anomalous) ---
        # IsolationForest score_samples returns negative path length;
        # we negate so higher = more anomalous.
        iso_raw = self.isolation_forest.score_samples(X)
        iso_scores = -iso_raw  # now higher = more outlier-like

        # LOF decision_function: negative for outliers, positive for inliers.
        # Negate so higher = more anomalous.
        lof_raw = self.lof.decision_function(X)
        lof_scores = -lof_raw

        # --- Class centroids in feature space ---
        centroids = self._compute_centroids(X, y, classes)

        signals = []
        for i in range(n_samples):
            proba = mean_proba[i]

            max_conf = float(np.max(proba))
            ent = float(scipy_entropy(proba + 1e-12))  # add epsilon to avoid log(0)

            sorted_proba = np.sort(proba)[::-1]
            margin = float(sorted_proba[0] - sorted_proba[1]) if len(sorted_proba) > 1 else 1.0

            disagreement = self._compute_disagreement(per_model_proba, i)

            pred_class_idx = int(np.argmax(proba))
            pred_class = classes[pred_class_idx]
            centroid = centroids.get(pred_class)
            if centroid is not None:
                centroid_dist = float(np.linalg.norm(X[i] - centroid))
            else:
                centroid_dist = 0.0

            signals.append({
                "max_confidence": max_conf,
                "entropy": ent,
                "margin": margin,
                "disagreement": disagreement,
                "isolation_score": float(iso_scores[i]),
                "lof_score": float(lof_scores[i]),
                "centroid_dist": centroid_dist,
            })

        return signals

    def _compute_centroids(
        self, X: np.ndarray, y: np.ndarray, classes: np.ndarray
    ) -> Dict:
        """
        Compute per-class mean vector (centroid) in feature space.

        Parameters
        ----------
        X : np.ndarray
        y : np.ndarray
        classes : np.ndarray

        Returns
        -------
        Dict[class_label, np.ndarray]
        """
        centroids = {}
        for cls in classes:
            mask = y == cls
            if mask.sum() > 0:
                centroids[cls] = X[mask].mean(axis=0)
        return centroids

    def _compute_disagreement(
        self, per_model_proba: List[np.ndarray], sample_idx: int
    ) -> float:
        """
        Compute mean pairwise L2 distance between model probability vectors
        for a single sample. Higher value = more disagreement.

        Parameters
        ----------
        per_model_proba : List[np.ndarray]
        sample_idx : int

        Returns
        -------
        float
        """
        vectors = [p[sample_idx] for p in per_model_proba]
        n = len(vectors)
        if n < 2:
            return 0.0
        total = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                total += float(np.linalg.norm(vectors[i] - vectors[j]))
                count += 1
        return total / count if count > 0 else 0.0
