"""
ensemble.py
-----------
Manages the ensemble of classifiers (RandomForest, GradientBoosting,
LogisticRegression, plus any custom models).

Each model is wrapped so the engine can call predict_proba uniformly.
Ensemble predictions are aggregated by averaging class probabilities.

Connects to: preprocessing.py (consumes transformed data),
             signal_extraction.py (provides per-model probabilities).
"""

import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression


class EnsembleClassifier:
    """
    Manages a collection of sklearn-compatible classifiers and exposes
    methods for training, individual prediction, and ensemble averaging.

    Parameters
    ----------
    custom_models : Optional[List]
        Additional sklearn-compatible classifiers with fit/predict_proba API.
    random_state : int
        Seed used for reproducibility across all default models.
        Default: 42.
    n_estimators : int
        Number of trees for RandomForest and  HistGradientBoosting
        Default: 100.
    """

    def __init__(
        self,
        custom_models: Optional[List] = None,
        random_state: int = 42,
        n_estimators: int = 100,
    ) -> None:
        self.random_state = random_state
        self.n_estimators = n_estimators
        self.classes_: Optional[np.ndarray] = None

        # Default models cover diverse inductive biases:
        # RF for variance reduction, GB for sequential bias correction,
        # LR for a linear baseline useful in high-dim feature spaces.
        self.models: List[Any] = [
                RandomForestClassifier(
                    n_estimators=50,          # was 100 — 50 is sufficient for noise detection
                    random_state=random_state,
                    n_jobs=-1,
                ),
                HistGradientBoostingClassifier(  # was GradientBoostingClassifier — 10-20x faster
                    max_iter=50,               # equivalent to n_estimators
                    random_state=random_state,
                ),
                LogisticRegression(
                    max_iter=1000,
                    random_state=random_state,
                    multi_class="auto",
                    solver="lbfgs",
                    n_jobs=-1,
                ),
            ]

        if custom_models:
            self.models.extend(custom_models)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Fit all classifiers on the transformed feature matrix.

        Parameters
        ----------
        X : np.ndarray
            Preprocessed feature matrix.
        y : np.ndarray
            Target label array.
        """
        self.classes_ = np.unique(y)
        for model in self.models:
            model.fit(X, y)

    def predict_proba_all(self, X: np.ndarray) -> List[np.ndarray]:
        """
        Return per-model probability matrices.

        Parameters
        ----------
        X : np.ndarray

        Returns
        -------
        List[np.ndarray]
            Each element is shape (n_samples, n_classes).
        """
        return [model.predict_proba(X) for model in self.models]

    def predict_proba_mean(self, X: np.ndarray) -> np.ndarray:
        """
        Average probability predictions across all models.

        Parameters
        ----------
        X : np.ndarray

        Returns
        -------
        np.ndarray
            Shape (n_samples, n_classes). Averaged probabilities.
        """
        all_proba = self.predict_proba_all(X)
        return np.mean(all_proba, axis=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict labels by taking argmax of averaged probabilities.

        Parameters
        ----------
        X : np.ndarray

        Returns
        -------
        np.ndarray
            Predicted class labels.
        """
        mean_proba = self.predict_proba_mean(X)
        indices = np.argmax(mean_proba, axis=1)
        return self.classes_[indices]

    def get_model_names(self) -> List[str]:
        """Return a list of model class names for logging purposes."""
        return [type(m).__name__ for m in self.models]

    def model_count(self) -> int:
        """Return the number of models in the ensemble."""
        return len(self.models)
