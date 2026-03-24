"""
review_builder.py
-----------------
Constructs human-readable review payloads for a given sample.

Provides generate_review_payload(sample_id) which aggregates:
  - Raw feature values from the original DataFrame.
  - Original and predicted labels.
  - Meta-model noise probability.
  - All signal values.
  - Per-model probability distributions.

The payload is designed to give a reviewer everything needed to make
an informed decision about whether a label correction is warranted.

Connects to: signal_extraction.py, meta_model.py, ensemble.py, engine.py.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


class ReviewPayloadBuilder:
    """
    Assembles rich review payloads for human-in-the-loop review.

    Parameters
    ----------
    None — all required data is passed at call time to keep this class stateless.
    """

    def build(
        self,
        sample_id: int,
        X_original: pd.DataFrame,
        y_original: pd.Series,
        predicted_label: Any,
        noise_probability: float,
        signal_dict: Dict[str, float],
        per_model_proba: List[np.ndarray],
        classes: np.ndarray,
        model_names: List[str],
    ) -> Dict[str, Any]:
        """
        Build the review payload for a specific sample.

        Parameters
        ----------
        sample_id : int
            Index into X_original / y_original.
        X_original : pd.DataFrame
            Original (non-transformed) feature DataFrame.
        y_original : pd.Series
            Original labels.
        predicted_label : Any
            Ensemble's predicted label.
        noise_probability : float
            Meta-model P(noise).
        signal_dict : Dict[str, float]
            Signal values for this sample.
        per_model_proba : List[np.ndarray]
            Per-model probability matrices (all samples).
        classes : np.ndarray
            Ordered class labels.
        model_names : List[str]
            Names of models in the ensemble.

        Returns
        -------
        Dict[str, Any]
            JSON-serializable review payload.
        """
        original_features = X_original.loc[sample_id].to_dict()
        # Ensure values are JSON-serializable (convert numpy scalars)
        original_features = {
            k: (v.item() if hasattr(v, "item") else v)
            for k, v in original_features.items()
        }

        original_label = y_original.loc[sample_id]
        if hasattr(original_label, "item"):
            original_label = original_label.item()

        if hasattr(predicted_label, "item"):
            predicted_label = predicted_label.item()

        # Find integer position of sample_id in the index
        sample_pos = list(X_original.index).index(sample_id)

        # Build per-model probability entries
        model_probabilities = []
        for model_name, proba_matrix in zip(model_names, per_model_proba):
            proba_vec = proba_matrix[sample_pos].tolist()
            model_probabilities.append({
                "model": model_name,
                "class_labels": [
                    (c.item() if hasattr(c, "item") else c) for c in classes
                ],
                "probabilities": proba_vec,
            })

        return {
            "original_features": original_features,
            "original_label": original_label,
            "predicted_label": predicted_label,
            "noise_probability": float(noise_probability),
            "signals": signal_dict,
            "model_probabilities": model_probabilities,
        }
