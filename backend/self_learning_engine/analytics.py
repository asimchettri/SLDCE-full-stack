"""
analytics.py
------------
Accumulates per-cycle snapshots of metrics and threshold values to build
longitudinal analytics history.

Provides get_analytics() which returns a JSON-serializable dict of all
historical time series for dashboard consumption.

Connects to: metrics.py (receives metric snapshots), decision.py (threshold snapshots),
             engine.py (called at the end of each cycle).
"""

from typing import Dict, List, Any


class AnalyticsTracker:
    """
    Records metric snapshots after every training/feedback cycle.

    Attributes
    ----------
    history : List[Dict]
        One entry per cycle containing all metrics for that cycle.
    """

    def __init__(self) -> None:
        self.history: List[Dict] = []

    def record_cycle(
        self,
        cycle_number: int,
        model_metrics: Dict[str, Any],
        correction_metrics: Dict[str, float],
        threshold: float,
        n_flagged: int,
    ) -> None:
        """
        Store a snapshot for the completed cycle.

        Parameters
        ----------
        cycle_number : int
        model_metrics : Dict
        correction_metrics : Dict
        threshold : float
            Current threshold after adaptation.
        n_flagged : int
            Number of samples flagged this cycle.
        """
        self.history.append({
            "cycle": cycle_number,
            "threshold": threshold,
            "n_flagged": n_flagged,
            **model_metrics,
            **correction_metrics,
        })

    def get_series(self, key: str) -> List[Any]:
        """
        Extract a named time series from history.

        Parameters
        ----------
        key : str
            Metric name (e.g. 'accuracy', 'f1_macro', 'threshold').

        Returns
        -------
        List[Any]
            Values ordered by cycle.
        """
        return [entry.get(key) for entry in self.history]

    def get_analytics(self) -> Dict[str, Any]:
        """
        Return all analytics as a JSON-serializable dict.

        Returns
        -------
        Dict with keys:
          - full_history: List[Dict] of all cycle snapshots
          - threshold_history: List[float]
          - accuracy_history: List[float]
          - f1_macro_history: List[float]
          - correction_precision_history: List[float]
          - flagged_count_per_cycle: List[int]
          - total_cycles: int
        """
        return {
            "full_history": list(self.history),
            "threshold_history": self.get_series("threshold"),
            "accuracy_history": self.get_series("accuracy"),
            "f1_macro_history": self.get_series("f1_macro"),
            "correction_precision_history": self.get_series("correction_precision"),
            "flagged_count_per_cycle": self.get_series("n_flagged"),
            "total_cycles": len(self.history),
        }

    def cycle_count(self) -> int:
        """Return the number of cycles recorded so far."""
        return len(self.history)
