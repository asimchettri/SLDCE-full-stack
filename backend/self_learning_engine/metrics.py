"""
metrics.py
----------
Computes model performance metrics and correction quality metrics
after each training or feedback cycle.

Model metrics: accuracy, precision, recall, F1 (macro + weighted), confusion matrix.
Correction metrics: correction_precision, false_correction_rate,
                    review_agreement_rate, auto_approval_rate.

All return values are JSON-serializable dicts.

Connects to: ensemble.py (prediction source), feedback.py (correction events),
             analytics.py (stores history snapshots).
"""

import numpy as np
from typing import Dict, List, Any
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


class MetricsComputer:
    """
    Computes model and correction metrics from predictions and feedback records.
    """

    def compute_model_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        labels: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Compute classification metrics.

        Parameters
        ----------
        y_true : np.ndarray
        y_pred : np.ndarray
        labels : np.ndarray
            Ordered class labels for confusion matrix columns/rows.

        Returns
        -------
        Dict[str, Any]
            Keys: accuracy, precision_macro, precision_weighted,
                  recall_macro, recall_weighted, f1_macro, f1_weighted,
                  confusion_matrix.
        """
        cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

        zero_div = 0  # return 0 when a class has no predicted samples

        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision_macro": float(
                precision_score(y_true, y_pred, average="macro", zero_division=zero_div)
            ),
            "precision_weighted": float(
                precision_score(y_true, y_pred, average="weighted", zero_division=zero_div)
            ),
            "recall_macro": float(
                recall_score(y_true, y_pred, average="macro", zero_division=zero_div)
            ),
            "recall_weighted": float(
                recall_score(y_true, y_pred, average="weighted", zero_division=zero_div)
            ),
            "f1_macro": float(
                f1_score(y_true, y_pred, average="macro", zero_division=zero_div)
            ),
            "f1_weighted": float(
                f1_score(y_true, y_pred, average="weighted", zero_division=zero_div)
            ),
            "confusion_matrix": cm,
        }

    def compute_correction_metrics(
        self,
        feedback_records: List[Any],
        n_flagged: int,
    ) -> Dict[str, float]:
        """
        Compute correction quality metrics from feedback records.

        Definitions:
          correction_precision = approved / (approved + rejected)
            "Of all corrections the engine proposed, how many were real noise?"
          false_correction_rate = rejected / (approved + rejected)
            "How often did the engine flag a clean sample as noisy?"
          review_agreement_rate = (approved + rejected) / n_flagged
            "What fraction of flagged samples received a definitive answer?"
          auto_approval_rate = approved / n_flagged
            "What fraction of all flagged samples were approved corrections?"

        Parameters
        ----------
        feedback_records : List[FeedbackRecord]
        n_flagged : int
            Total samples flagged in this cycle.

        Returns
        -------
        Dict[str, float]
        """
        approved = sum(1 for r in feedback_records if r.decision_type == "approve")
        rejected = sum(1 for r in feedback_records if r.decision_type == "reject")
        modified = sum(1 for r in feedback_records if r.decision_type == "modify")
        uncertain = sum(1 for r in feedback_records if r.decision_type == "uncertain")

        definitive = approved + rejected
        correction_precision = approved / definitive if definitive > 0 else 0.0
        false_correction_rate = rejected / definitive if definitive > 0 else 0.0
        review_agreement_rate = definitive / n_flagged if n_flagged > 0 else 0.0
        auto_approval_rate = approved / n_flagged if n_flagged > 0 else 0.0

        return {
            "correction_precision": float(correction_precision),
            "false_correction_rate": float(false_correction_rate),
            "review_agreement_rate": float(review_agreement_rate),
            "auto_approval_rate": float(auto_approval_rate),
            "approved_count": approved,
            "rejected_count": rejected,
            "modified_count": modified,
            "uncertain_count": uncertain,
        }
