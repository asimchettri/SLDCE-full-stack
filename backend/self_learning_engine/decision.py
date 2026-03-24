"""
decision.py
-----------
Maintains an adaptive noise threshold and decides which samples to flag
for human review.

Threshold adaptation logic:
  - If correction_precision < previous: noise threshold increases (become stricter
    to avoid flagging clean samples = fewer false positives).
  - If correction_precision >= previous: noise threshold decreases slightly
    (become more lenient to catch more noisy samples = higher recall).
  - Threshold is clamped to [min_threshold, max_threshold] at all times.

Connects to: meta_model.py (input noise probabilities), engine.py (receives updates).
"""

from typing import Optional


class DecisionController:
    """
    Maintains an adaptive decision threshold for flagging noisy samples.

    Parameters
    ----------
    initial_threshold : float
        Starting noise probability threshold. Default: 0.5.
    min_threshold : float
        Lower bound for threshold adaptation.
        Prevents threshold from becoming too permissive.
        Default: 0.2.
    max_threshold : float
        Upper bound for threshold adaptation.
        Prevents threshold from becoming so strict nothing gets flagged.
        Default: 0.9.
    increase_step : float
        Amount to raise threshold when precision decreases.
        Default: 0.05.
    decrease_step : float
        Amount to lower threshold when precision improves.
        Default: 0.02.
    """

    def __init__(
        self,
        initial_threshold: float = 0.5,
        min_threshold: float = 0.2,
        max_threshold: float = 0.9,
        increase_step: float = 0.05,
        decrease_step: float = 0.02,
    ) -> None:
        self._initial_threshold = initial_threshold 
        self.threshold = initial_threshold
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.increase_step = increase_step
        self.decrease_step = decrease_step

        self._previous_precision: Optional[float] = None
        self._threshold_history: list = [initial_threshold]

    def reset(self) -> None:
        """Reset threshold to initial value. Called on fresh engine fit."""
        self.threshold = self._initial_threshold
        self._previous_precision = None
        self._threshold_history = [self._initial_threshold] 
        
           

    def should_flag(self, noise_probability: float) -> bool:
        """
        Decide whether a sample should be flagged for review.

        Parameters
        ----------
        noise_probability : float
            P(label is noisy) from the meta-model.

        Returns
        -------
        bool
        """
        return noise_probability >= self.threshold

    def update(self, correction_precision: float) -> None:
        """
        Adapt the threshold based on correction precision from the last cycle.

        If precision dropped → raise threshold (stricter, fewer flags, higher precision).
        If precision improved or held → lower threshold (more permissive, more recall).

        Parameters
        ----------
        correction_precision : float
            Fraction of flagged-and-confirmed corrections in the last cycle.
            Range [0, 1].
        """
        if self._previous_precision is not None:
            if correction_precision < self._previous_precision:
                self.threshold = min(
                    self.threshold + self.increase_step, self.max_threshold
                )
            else:
                self.threshold = max(
                    self.threshold - self.decrease_step, self.min_threshold
                )

        self._previous_precision = correction_precision
        self._threshold_history.append(self.threshold)

    def current_threshold(self) -> float:
        """Return the current threshold value."""
        return self.threshold

    def threshold_history(self) -> list:
        """Return the list of all historical threshold values."""
        return list(self._threshold_history)
