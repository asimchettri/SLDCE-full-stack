"""
ML Integration Layer - Clean Integration with Dev 1's Pipeline
Bridges Full-Stack backend with Dev 1's ML code
"""
import os
import sys
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import yaml
import json
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Add ML pipeline to Python path
ML_PIPELINE_PATH = Path(__file__).parent.parent / "ml_pipeline"
sys.path.insert(0, str(ML_PIPELINE_PATH))
sys.path.insert(0, str(ML_PIPELINE_PATH / "src"))
sys.path.insert(0, str(ML_PIPELINE_PATH / "src" / "data"))

# Import Dev 1's modules
try:
    from model_trainer import get_model
    from detectors import (
        detect_confidence_issues,
        detect_anomalies,
        combine_signals,
        generate_suggestions
    )
except ImportError as e:
    logger.error(f"Failed to import ML modules: {e}")
    raise


class MLIntegration:
    """
    Integration wrapper using Dev 1's ACTUAL ML pipeline
    Provides a clean interface between FastAPI backend and ML notebooks
    """
    
    def __init__(self):
        self.ml_path = ML_PIPELINE_PATH
        self.config = self._load_config()
        self.model = None
        
    def _load_config(self) -> Dict:
        """Load ML pipeline configuration"""
        config_path = self.ml_path / "config" / "default.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default config if file doesn't exist
        return {
            "model": {
                "name": "random_forest",
                "params": {"n_estimators": 100, "random_state": 42}
            },
            "signals": {
                "confidence_threshold": 0.7,
                "anomaly_contamination": 0.1
            },
            "fusion": {
                "confidence_weight": 0.6,
                "anomaly_weight": 0.4
            },
            "decision": {
                "reject_threshold": 0.8
            }
        }
    
    def _samples_to_arrays(self, samples: List[Any]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert Sample SQLAlchemy objects to numpy arrays
        
        Args:
            samples: List of Sample objects from database
            
        Returns:
            (X, y) tuple of feature matrix and labels
        """
        features = []
        labels = []
        
        for sample in samples:
            # Parse JSON features
            feat = json.loads(sample.features)
            features.append(feat)
            labels.append(sample.current_label)
        
        return np.array(features), np.array(labels)
    
    def _determine_signal_source(self, conf_flag: bool, anom_flag: bool) -> str:
        """Determine which signals flagged the sample"""
        if conf_flag and anom_flag:
            return "both"
        elif conf_flag:
            return "confidence"
        elif anom_flag:
            return "anomaly"
        else:
            return "none"
    
    def run_full_detection(
        self,
        samples: List[Any],
        priority_weights: Optional[Dict[str, float]] = None,
        confidence_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Run complete detection pipeline using Dev 1's code
        
        Pipeline Steps:
        1. Convert samples to arrays
        2. Train model (Notebook 02)
        3. Confidence detection (Notebook 03)
        4. Anomaly detection (Notebook 04)
        5. Signal fusion (Notebook 05)
        6. Generate suggestions (Notebook 06)
        
        Args:
            samples: List of Sample objects from database
            priority_weights: Optional custom weights for signal fusion
            confidence_threshold: Optional custom confidence threshold
            
        Returns:
            List of detection results with all signals combined
        """
        # Validate input
        if not samples or len(samples) < 10:
            logger.warning(f"Insufficient samples for detection: {len(samples) if samples else 0}")
            return []
        
        # Convert to arrays
        try:
            X, y = self._samples_to_arrays(samples)
        except Exception as e:
            logger.error(f"Failed to convert samples to arrays: {e}")
            raise
        
        # Get configuration
        model_name = self.config.get("model", {}).get("name", "random_forest")
        model_params = self.config.get("model", {}).get("params", {
            "n_estimators": 100, 
            "random_state": 42
        })
        
        conf_threshold = confidence_threshold or self.config.get(
            "signals", {}
        ).get("confidence_threshold", 0.7)
        
        anom_contamination = self.config.get(
            "signals", {}
        ).get("anomaly_contamination", 0.1)
        
        # Set fusion weights
        if priority_weights is None:
            conf_w = self.config.get("fusion", {}).get("confidence_weight", 0.6)
            anom_w = self.config.get("fusion", {}).get("anomaly_weight", 0.4)
        else:
            conf_w = priority_weights.get("confidence", 0.6)
            anom_w = priority_weights.get("anomaly", 0.4)
        
        logger.info(f"Running detection on {len(samples)} samples with {model_name}")
        
        # === STEP 1: Train Model (Dev 1's Notebook 02) ===
        try:
            model = get_model(model_name, model_params)
            model.train(X, y)
            self.model = model
            logger.info("Model training complete")
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise
        
        # === STEP 2: Confidence Detection (Dev 1's Notebook 03) ===
        try:
            confidence_df = detect_confidence_issues(
                model, X, y, conf_threshold
            )
            logger.info(f"Confidence detection complete: {confidence_df['confidence_flag'].sum()} flags")
        except Exception as e:
            logger.error(f"Confidence detection failed: {e}")
            raise
        
        # === STEP 3: Anomaly Detection (Dev 1's Notebook 04) ===
        try:
            anomaly_df = detect_anomalies(X, anom_contamination)
            logger.info(f"Anomaly detection complete: {anomaly_df['anomaly_flag'].sum()} flags")
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            raise
        
        # === STEP 4: Combine Signals (Dev 1's Notebook 05) ===
        try:
            combined_df = combine_signals(
                confidence_df,
                anomaly_df,
                conf_w,
                anom_w
            )
            logger.info("Signal fusion complete")
        except Exception as e:
            logger.error(f"Signal combination failed: {e}")
            raise
        
        # === STEP 5: Generate Suggestions (Dev 1's Notebook 06) ===
        try:
            reject_thresh = self.config.get("decision", {}).get("reject_threshold", 0.8)
            review_thresh = reject_thresh / 2
            
            suggestions_df = generate_suggestions(
                combined_df,
                reject_thresh,
                review_thresh
            )
            logger.info("Suggestion generation complete")
        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            raise
        
        # === STEP 6: Convert to output format ===
        results = []
        for i, sample in enumerate(samples):
            try:
                results.append({
                    'sample_id': sample.id,
                    'predicted_label': int(confidence_df.iloc[i]['predicted_label']),
                    'confidence_score': float(confidence_df.iloc[i]['predicted_label_confidence']),
                    'anomaly_score': float(anomaly_df.iloc[i]['anomaly_score']),
                    'priority_score': float(combined_df.iloc[i]['combined_risk_score']),
                    'suggestion': suggestions_df.iloc[i]['suggestion'],
                    'reason': suggestions_df.iloc[i]['decision_reason'],
                    'flagged_by': self._determine_signal_source(
                        confidence_df.iloc[i]['confidence_flag'],
                        anomaly_df.iloc[i]['anomaly_flag']
                    ),
                    'signal_breakdown': {
                        'confidence': float(confidence_df.iloc[i]['predicted_label_confidence']),
                        'anomaly': float(anomaly_df.iloc[i]['anomaly_score']),
                        'confidence_flag': bool(confidence_df.iloc[i]['confidence_flag']),
                        'anomaly_flag': bool(anomaly_df.iloc[i]['anomaly_flag']),
                        'weights_used': {'confidence': conf_w, 'anomaly': anom_w}
                    }
                })
            except Exception as e:
                logger.error(f"Failed to process sample {sample.id}: {e}")
                continue
        
        logger.info(f"Detection complete: {len(results)} results generated")
        return results
    
    def evaluate_model(
        self,
        X: np.ndarray,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, float]:
        """
        Calculate evaluation metrics (from Dev 1's Notebook 09)
        
        Returns accuracy, precision, recall, F1-score
        """
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score
        )
        
        return {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, average='weighted', zero_division=0)),
            'f1_score': float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
        }


# Singleton instance for reuse
_ml_integration_instance = None

def get_ml_integration() -> MLIntegration:
    """Get singleton ML integration instance"""
    global _ml_integration_instance
    if _ml_integration_instance is None:
        _ml_integration_instance = MLIntegration()
    return _ml_integration_instance