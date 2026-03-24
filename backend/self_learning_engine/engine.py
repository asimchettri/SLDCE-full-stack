"""
engine.py
---------
SelfLearningCorrectionEngine: top-level orchestrator that wires together
all subsystems to provide a clean public API.

Public methods:
  fit(X, y)                    — Initial training pass.
  detect_noise(X, y)           — Flag suspicious samples.
  generate_review_payload(id)  — Build reviewer context dict.
  apply_feedback(...)          — Store human decision.
  update_meta_model()          — Retrain meta-model on feedback.
  update_threshold()           — Adapt decision threshold.
  retrain_if_ready()           — Retrain ensemble if enough corrections.
  get_metrics()                — Latest model + correction metrics.
  get_analytics()              — Full longitudinal analytics.

Design:
  - No global state; all state lives in instance attributes.
  - Engine holds references to subsystem objects.
  - Thin wrapper: orchestrates calls, delegates logic.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional

from self_learning_engine.preprocessing import DataPreprocessor
from self_learning_engine.ensemble import EnsembleClassifier
from self_learning_engine.signal_extraction import SignalExtractor
from self_learning_engine.signal_vector import SignalVectorBuilder
from self_learning_engine.meta_model import MetaNoiseModel
from self_learning_engine.decision import DecisionController
from self_learning_engine.feedback import FeedbackRecord, FeedbackStore
from self_learning_engine.metrics import MetricsComputer
from self_learning_engine.analytics import AnalyticsTracker
from self_learning_engine.retraining import RetrainingManager
from self_learning_engine.review_builder import ReviewPayloadBuilder


class SelfLearningCorrectionEngine:
    """
    Self-Learning Data Correction Engine for tabular classification datasets.

    Detects potentially mislabeled samples using ensemble disagreement and
    anomaly signals, learns from human reviewer feedback, and progressively
    corrects the dataset through supervised retraining.

    Parameters
    ----------
    custom_models : Optional[List]
        Additional sklearn-compatible classifiers to include in the ensemble.
    contamination : float
        Expected fraction of anomalies for IsolationForest and LOF. Default: 0.1.
    initial_threshold : float
        Starting noise decision threshold. Default: 0.5.
    min_threshold : float
        Lower bound for threshold. Default: 0.2.
    max_threshold : float
        Upper bound for threshold. Default: 0.9.
    threshold_increase_step : float
        Threshold increase when precision drops. Default: 0.05.
    threshold_decrease_step : float
        Threshold decrease when precision improves. Default: 0.02.
    min_corrections_to_retrain : int
        Minimum corrections before retraining ensemble. Default: 5.
    n_estimators : int
        Trees for RandomForest and GradientBoosting. Default: 100.
    random_state : int
        Global seed. Default: 42.
    """

    def __init__(
        self,
        custom_models: Optional[List] = None,
        contamination: float = 0.1,
        initial_threshold: float = 0.5,
        min_threshold: float = 0.2,
        max_threshold: float = 0.9,
        threshold_increase_step: float = 0.05,
        threshold_decrease_step: float = 0.02,
        min_corrections_to_retrain: int = 5,
        n_estimators: int = 100,
        random_state: int = 42,
    ) -> None:
        self._preprocessor = DataPreprocessor()
        self._ensemble = EnsembleClassifier(
            custom_models=custom_models,
            random_state=random_state,
            n_estimators=n_estimators,
        )
        self._signal_extractor = SignalExtractor(
            contamination=contamination,
            random_state=random_state,
        )
        self._signal_builder = SignalVectorBuilder()
        self._meta_model = MetaNoiseModel(random_state=random_state)
        self._decision = DecisionController(
            initial_threshold=initial_threshold,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
            increase_step=threshold_increase_step,
            decrease_step=threshold_decrease_step,
        )
        self._feedback_store = FeedbackStore()
        self._metrics_computer = MetricsComputer()
        self._analytics = AnalyticsTracker()
        self._retraining_manager = RetrainingManager(
            min_corrections_to_retrain=min_corrections_to_retrain
        )
        self._review_builder = ReviewPayloadBuilder()

        # Runtime state populated after fit()
        self._X_original: Optional[pd.DataFrame] = None
        self._y_original: Optional[pd.Series] = None
        self._X_transformed: Optional[np.ndarray] = None

        # Populated after detect_noise()
        self._last_signals: Optional[List[Dict]] = None
        self._last_signal_matrix: Optional[np.ndarray] = None
        self._last_noise_probs: Optional[np.ndarray] = None
        self._last_predictions: Optional[np.ndarray] = None
        self._last_per_model_proba: Optional[List[np.ndarray]] = None
        self._last_mean_proba: Optional[np.ndarray] = None
        self._last_n_flagged: int = 0

        # Latest metrics dict
        self._latest_metrics: Optional[Dict] = None
        self._fitted = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """
        Preprocess data, train ensemble, and fit anomaly detectors.

        Parameters
        ----------
        X : pd.DataFrame
            Feature DataFrame (numeric + categorical supported).
        y : pd.Series
            Target labels.
        """
        self._X_original = X.copy()
        self._y_original = y.copy()

        self._X_transformed = self._preprocessor.fit_transform(X)
        self._ensemble.fit(self._X_transformed, y.values)
        self._signal_extractor.fit(self._X_transformed)

        # Compute initial model metrics
        y_pred = self._ensemble.predict(self._X_transformed)
        model_metrics = self._metrics_computer.compute_model_metrics(
            y.values, y_pred, self._ensemble.classes_
        )
        self._latest_metrics = {"model": model_metrics, "correction": {}}
        self._fitted = True
        self._decision.reset() 

    def detect_noise(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Compute noise signals and flag samples exceeding the current threshold.

        Parameters
        ----------
        X : pd.DataFrame
        y : pd.Series

        Returns
        -------
        Dict with keys:
          - flagged_samples: list of {sample_id, noise_probability,
                                      predicted_label, original_label}
          - current_threshold: float
        """
        self._require_fitted()

        X_transformed = self._preprocessor.transform(X)
        per_model_proba = self._ensemble.predict_proba_all(X_transformed)
        mean_proba = self._ensemble.predict_proba_mean(X_transformed)
        predictions = self._ensemble.predict(X_transformed)

        signals = self._signal_extractor.compute_signals(
            X_transformed,
            y.values,
            per_model_proba,
            mean_proba,
            self._ensemble.classes_,
        )
        signal_matrix = self._signal_builder.build_matrix(signals)
        noise_probs = self._meta_model.predict_noise_probabilities(signal_matrix)

        # Cache for review payload generation
        self._last_signals = signals
        self._last_signal_matrix = signal_matrix
        self._last_noise_probs = noise_probs
        self._last_predictions = predictions
        self._last_per_model_proba = per_model_proba
        self._last_mean_proba = mean_proba

        flagged = []
        for i, (sample_id, noise_prob) in enumerate(zip(X.index, noise_probs)):
            if self._decision.should_flag(noise_prob):
                pred = predictions[i]
                orig = y.iloc[i]
                flagged.append({
                    "sample_id": int(sample_id),
                    "noise_probability": float(noise_prob),
                    "predicted_label": pred.item() if hasattr(pred, "item") else pred,
                    "original_label": orig.item() if hasattr(orig, "item") else orig,
                })

        self._last_n_flagged = len(flagged)

        return {
            "flagged_samples": flagged,
            "current_threshold": self._decision.current_threshold(),
        }

    def generate_review_payload(self, sample_id: int) -> Dict:
        """
        Generate a rich context payload for a specific sample.

        Must be called after detect_noise().

        Parameters
        ----------
        sample_id : int
            Index value in the original DataFrame.

        Returns
        -------
        Dict with keys:
          original_features, original_label, predicted_label,
          noise_probability, signals, model_probabilities.
        """
        self._require_fitted()
        if self._last_signals is None:
            raise RuntimeError("detect_noise() must be called before generate_review_payload().")

        sample_pos = list(self._X_original.index).index(sample_id)

        return self._review_builder.build(
            sample_id=sample_id,
            X_original=self._X_original,
            y_original=self._y_original,
            predicted_label=self._last_predictions[sample_pos],
            noise_probability=float(self._last_noise_probs[sample_pos]),
            signal_dict=self._last_signals[sample_pos],
            per_model_proba=self._last_per_model_proba,
            classes=self._ensemble.classes_,
            model_names=self._ensemble.get_model_names(),
        )

    def apply_feedback(
        self,
        sample_id: int,
        previous_label: Any,
        updated_label: Any,
        decision_type: str,
        reviewer_comment: str = "",
        reviewer_confidence: float = 1.0,
    ) -> Dict:
        """
        Store a reviewer's decision for a flagged sample.

        Also registers the labeled example with the meta-model for later training.

        Parameters
        ----------
        sample_id : int
        previous_label : Any
        updated_label : Any
        decision_type : str
            One of: 'approve', 'reject', 'modify', 'uncertain'.
        reviewer_comment : str
        reviewer_confidence : float

        Returns
        -------
        Dict
            The stored feedback record as a dict.
        """
        self._require_fitted()

        if self._last_signals is None:
            raise RuntimeError("detect_noise() must be called before apply_feedback().")

        sample_pos = list(self._X_original.index).index(sample_id)
        noise_prob = float(self._last_noise_probs[sample_pos])
        signal_dict = self._last_signals[sample_pos]
        signal_vector = self._signal_builder.build_vector(signal_dict)

        record = FeedbackRecord(
            sample_id=sample_id,
            previous_label=previous_label,
            updated_label=updated_label,
            decision_type=decision_type,
            reviewer_comment=reviewer_comment,
            reviewer_confidence=reviewer_confidence,
            noise_probability_at_review=noise_prob,
            signal_snapshot=signal_dict,
        )
        self._feedback_store.add(record)

        # Feed meta-model: approve = noisy, reject = clean
        is_noisy = decision_type in {"approve", "modify"}
        self._meta_model.add_feedback(signal_vector, is_noisy)

        return record.to_dict()

    def update_meta_model(self) -> Dict:
        """
        Retrain the meta-model on all accumulated feedback.

        Returns
        -------
        Dict
            {'trained': bool, 'feedback_count': int}
        """
        trained = self._meta_model.train()
        return {
            "trained": trained,
            "feedback_count": self._meta_model.feedback_count(),
        }

    def update_threshold(self) -> Dict:
        """
        Adapt the decision threshold based on latest correction precision.

        Should be called after a feedback cycle is complete.

        Returns
        -------
        Dict
            {'previous_threshold': float, 'new_threshold': float,
             'correction_precision': float}
        """
        previous = self._decision.current_threshold()

        confirmed = self._feedback_store.get_pending_for_retrain()
        correction_metrics = self._metrics_computer.compute_correction_metrics(
            self._feedback_store.records,
            self._last_n_flagged,
        )
        cp = correction_metrics["correction_precision"]
        self._decision.update(cp)

        return {
            "previous_threshold": float(previous),
            "new_threshold": self._decision.current_threshold(),
            "correction_precision": float(cp),
        }

    def retrain_if_ready(self) -> Dict:
        """
        Retrain the ensemble if enough confirmed corrections are available.

        Returns
        -------
        Dict
            {'retrained': bool, 'cycle_number': int, 'corrections_applied': int}
        """
        self._require_fitted()

        confirmed = self._feedback_store.get_pending_for_retrain()
        if not self._retraining_manager.should_retrain(confirmed):
            return {
                "retrained": False,
                "cycle_number": self._retraining_manager.cycle_number,
                "corrections_applied": len(confirmed),
            }

        X_corrected, y_corrected = self._retraining_manager.prepare_corrected_dataset(
            self._X_original, self._y_original, confirmed
        )

        cycle = self._retraining_manager.retrain(
            self._ensemble, self._preprocessor, X_corrected, y_corrected
        )

        # Refit anomaly detectors on new data
        self._X_transformed = self._preprocessor.transform(X_corrected)
        self._signal_extractor.fit(self._X_transformed)

        # Update working copies to reflect applied corrections
        self._X_original = X_corrected
        self._y_original = y_corrected

        # Recompute model metrics
        y_pred = self._ensemble.predict(self._X_transformed)
        model_metrics = self._metrics_computer.compute_model_metrics(
            y_corrected.values, y_pred, self._ensemble.classes_
        )
        correction_metrics = self._metrics_computer.compute_correction_metrics(
            self._feedback_store.records,
            self._last_n_flagged,
        )
        self._latest_metrics = {
            "model": model_metrics,
            "correction": correction_metrics,
        }

        self._analytics.record_cycle(
            cycle_number=cycle,
            model_metrics=model_metrics,
            correction_metrics=correction_metrics,
            threshold=self._decision.current_threshold(),
            n_flagged=self._last_n_flagged,
        )

        return {
            "retrained": True,
            "cycle_number": cycle,
            "corrections_applied": len(confirmed),
        }

    def get_metrics(self) -> Dict:
        """
        Return the most recent model and correction metrics.

        Returns
        -------
        Dict with keys: 'model' (classification metrics), 'correction' (quality metrics).
        """
        if self._latest_metrics is None:
            return {"model": {}, "correction": {}}
        return self._latest_metrics

    def get_analytics(self) -> Dict:
        """
        Return full longitudinal analytics history.

        Returns
        -------
        Dict with history arrays for accuracy, F1, threshold, etc.
        """
        return self._analytics.get_analytics()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _require_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError("Engine not fitted. Call fit(X, y) first.")
