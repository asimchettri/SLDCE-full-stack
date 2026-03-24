"""
retraining.py
-------------
Manages safe ensemble retraining using validated corrections.

Key safety rules:
  1. Never mutate the original DataFrame passed by the caller.
  2. Apply approved corrections to a working copy only.
  3. Only retrain when new confirmed corrections exist (avoid wasted cycles).
  4. Log each retraining cycle number.

Connects to: feedback.py (source of corrections), ensemble.py (model to retrain),
             preprocessing.py (preprocessing pipeline), engine.py (orchestration).
"""

import pandas as pd
import numpy as np
from typing import List, Any

from self_learning_engine.feedback import FeedbackRecord


class RetrainingManager:
    """
    Applies confirmed label corrections to a safe working copy of the dataset
    and triggers ensemble retraining.

    Parameters
    ----------
    min_corrections_to_retrain : int
        Minimum new approved/modified corrections required before retraining.
        Prevents unnecessary retraining on trivially few changes.
        Default: 5.
    """

    def __init__(self, min_corrections_to_retrain: int = 5) -> None:
        self.min_corrections_to_retrain = min_corrections_to_retrain
        self.cycle_number: int = 0
        self._applied_sample_ids: set = set()

    def prepare_corrected_dataset(
        self,
        X_original: pd.DataFrame,
        y_original: pd.Series,
        confirmed_records: List[FeedbackRecord],
    ):
        """
        Apply confirmed label corrections to a copy of the dataset.

        Parameters
        ----------
        X_original : pd.DataFrame
        y_original : pd.Series
        confirmed_records : List[FeedbackRecord]
            Records with decision_type in {'approve', 'modify'}.

        Returns
        -------
        Tuple[pd.DataFrame, pd.Series]
            (X_copy, y_corrected) — safe working copies.
        """
        X_copy = X_original.copy()
        y_copy = y_original.copy()

        new_records = [
            r for r in confirmed_records
            if r.sample_id not in self._applied_sample_ids
        ]

        for record in new_records:
            idx = record.sample_id
            if idx in y_copy.index:
                y_copy.at[idx] = record.updated_label
                self._applied_sample_ids.add(idx)

        return X_copy, y_copy

    def should_retrain(self, confirmed_records: List[FeedbackRecord]) -> bool:
        """
        Determine whether enough new corrections exist to justify retraining.

        Parameters
        ----------
        confirmed_records : List[FeedbackRecord]

        Returns
        -------
        bool
        """
        new_corrections = [
            r for r in confirmed_records
            if r.sample_id not in self._applied_sample_ids
        ]
        return len(new_corrections) >= self.min_corrections_to_retrain

    def retrain(
        self,
        ensemble,
        preprocessor,
        X_corrected: pd.DataFrame,
        y_corrected: pd.Series,
    ) -> int:
        """
        Refit the preprocessor and ensemble on corrected data.

        Parameters
        ----------
        ensemble : EnsembleClassifier
        preprocessor : DataPreprocessor
        X_corrected : pd.DataFrame
        y_corrected : pd.Series

        Returns
        -------
        int
            Updated cycle number after retraining.
        """
        X_transformed = preprocessor.fit_transform(X_corrected)
        ensemble.fit(X_transformed, y_corrected.values)
        self.cycle_number += 1
        return self.cycle_number
