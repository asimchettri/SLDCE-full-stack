"""
feedback.py
-----------
Stores and manages human reviewer feedback for each flagged sample.

Each feedback record captures the full review context so the system can:
  1. Feed labeled examples to the meta-model.
  2. Compute correction metrics (precision, false correction rate, etc.).
  3. Audit all decisions for explainability.

Connects to: meta_model.py (provides training data), metrics.py (provides raw events),
             engine.py (receives feedback calls).
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Valid decision types — used for validation and metric bucketing.
VALID_DECISION_TYPES = {"approve", "reject", "modify", "uncertain"}


class FeedbackRecord:
    """
    Immutable value object representing a single reviewer decision.

    Parameters
    ----------
    sample_id : int
    previous_label : Any
    updated_label : Any
    decision_type : str
        One of: 'approve', 'reject', 'modify', 'uncertain'.
    reviewer_comment : str
    reviewer_confidence : float
        Reviewer's self-reported confidence in [0, 1].
    noise_probability_at_review : float
        Meta-model score at time of review.
    signal_snapshot : Dict[str, float]
        Copy of the signal dict at time of review.
    """

    def __init__(
        self,
        sample_id: int,
        previous_label: Any,
        updated_label: Any,
        decision_type: str,
        reviewer_comment: str,
        reviewer_confidence: float,
        noise_probability_at_review: float,
        signal_snapshot: Dict[str, float],
    ) -> None:
        if decision_type not in VALID_DECISION_TYPES:
            raise ValueError(
                f"decision_type must be one of {VALID_DECISION_TYPES}, got '{decision_type}'"
            )

        self.sample_id = sample_id
        self.previous_label = previous_label
        self.updated_label = updated_label
        self.decision_type = decision_type
        self.reviewer_comment = reviewer_comment
        self.reviewer_confidence = reviewer_confidence
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.noise_probability_at_review = noise_probability_at_review
        self.signal_snapshot = signal_snapshot

    def to_dict(self) -> Dict:
        """Serialize to a JSON-serializable dictionary."""
        return {
            "sample_id": self.sample_id,
            "previous_label": self.previous_label,
            "updated_label": self.updated_label,
            "decision_type": self.decision_type,
            "reviewer_comment": self.reviewer_comment,
            "reviewer_confidence": self.reviewer_confidence,
            "timestamp": self.timestamp,
            "noise_probability_at_review": self.noise_probability_at_review,
            "signal_snapshot": self.signal_snapshot,
        }


class FeedbackStore:
    """
    Stores all feedback records and provides query methods.

    Attributes
    ----------
    records : List[FeedbackRecord]
        All feedback records in insertion order.
    """

    def __init__(self) -> None:
        self.records: List[FeedbackRecord] = []

    def add(self, record: FeedbackRecord) -> None:
        """
        Add a new feedback record.

        Parameters
        ----------
        record : FeedbackRecord
        """
        self.records.append(record)

    def get_pending_for_retrain(self) -> List[FeedbackRecord]:
        """
        Return all approved or modified records usable for retraining.

        Only 'approve' and 'modify' decisions result in a confirmed label
        correction and are valid for supervised retraining.

        Returns
        -------
        List[FeedbackRecord]
        """
        return [r for r in self.records if r.decision_type in {"approve", "modify"}]

    def get_all(self) -> List[Dict]:
        """Return all records as a list of JSON-serializable dicts."""
        return [r.to_dict() for r in self.records]

    def count(self) -> int:
        """Return total number of feedback records."""
        return len(self.records)

    def count_by_decision(self) -> Dict[str, int]:
        """
        Count records grouped by decision type.

        Returns
        -------
        Dict[str, int]
            Example: {'approve': 10, 'reject': 3, 'modify': 2, 'uncertain': 1}
        """
        counts = {d: 0 for d in VALID_DECISION_TYPES}
        for r in self.records:
            counts[r.decision_type] += 1
        return counts
