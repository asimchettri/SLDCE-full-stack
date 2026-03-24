"""
signal_vector.py
----------------
Converts the per-sample signal dict (produced by SignalExtractor) into
a fixed-length numeric vector suitable for the meta-model.

Defines the canonical signal order so the meta-model always sees
a consistent feature space regardless of dict key ordering.

Connects to: signal_extraction.py (input), meta_model.py (output).
"""

import numpy as np
from typing import List, Dict

# Canonical order of signal keys used to build the feature vector.
# This ordering must remain stable across versions to avoid breaking
# a trained meta-model. New signals should be appended, not inserted.
SIGNAL_ORDER = [
    "max_confidence",
    "entropy",
    "margin",
    "disagreement",
    "isolation_score",
    "lof_score",
    "centroid_dist",
]


class SignalVectorBuilder:
    """
    Converts signal dicts into numeric arrays for the meta-model.

    Attributes
    ----------
    signal_order : List[str]
        Ordered list of signal names. Changing this order invalidates
        any previously trained meta-model.
    """

    def __init__(self) -> None:
        self.signal_order: List[str] = SIGNAL_ORDER

    def build_vector(self, signal_dict: Dict[str, float]) -> np.ndarray:
        """
        Convert a single signal dict to a 1-D numpy array.

        Parameters
        ----------
        signal_dict : Dict[str, float]

        Returns
        -------
        np.ndarray
            Shape (len(signal_order),).

        Raises
        ------
        KeyError
            If a required signal key is missing from signal_dict.
        """
        try:
            return np.array([signal_dict[k] for k in self.signal_order], dtype=np.float64)
        except KeyError as exc:
            raise KeyError(f"Signal key missing from signal dict: {exc}") from exc

    def build_matrix(self, signals: List[Dict[str, float]]) -> np.ndarray:
        """
        Convert a list of signal dicts to a 2-D matrix.

        Parameters
        ----------
        signals : List[Dict[str, float]]

        Returns
        -------
        np.ndarray
            Shape (n_samples, len(signal_order)).
        """
        return np.vstack([self.build_vector(s) for s in signals])

    def dimension(self) -> int:
        """Return the number of signals (feature dimensionality)."""
        return len(self.signal_order)
