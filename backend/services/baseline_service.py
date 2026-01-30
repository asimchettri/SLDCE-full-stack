"""
Baseline Training Service - Train model on clean dataset
CRITICAL: Establishes baseline performance before noise injection
"""
from sqlalchemy.orm import Session
from models.dataset import Sample
from models.model import MLModel
from fastapi import HTTPException
from typing import Dict, Any, Tuple
import numpy as np
import json
import logging
from datetime import datetime

from services.ml_integration import get_ml_integration

logger = logging.getLogger(__name__)


class BaselineService:
    """Service for training baseline models on clean data"""
    
    @staticmethod
    def train_baseline(
        db: Session,
        dataset_id: int,
        model_type: str = "random_forest",
        test_size: float = 0.2,
        hyperparameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Train baseline model on clean dataset
        
        This should be done BEFORE noise injection to establish
        true baseline performance on clean data.
        
        Args:
            db: Database session
            dataset_id: Dataset ID
            model_type: Model type ("random_forest", "logistic", "svm")
            test_size: Test split ratio (default: 0.2)
            hyperparameters: Optional custom hyperparameters
            
        Returns:
            Baseline model metrics and info
        """
        logger.info(f"🎯 Training baseline {model_type} on dataset {dataset_id}")
        
        # Check if baseline already exists
        existing_baseline = db.query(MLModel).filter(
            MLModel.dataset_id == dataset_id,
            MLModel.is_baseline == True,
            MLModel.is_active == True
        ).first()
        
        if existing_baseline:
            logger.warning(f"Baseline model already exists (ID: {existing_baseline.id})")
            raise HTTPException(
                status_code=400,
                detail=f"Baseline model already exists for this dataset. "
                       f"Delete it first if you want to retrain."
            )
        
        # Get all samples (should be clean at this point)
        samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id
        ).all()
        
        if not samples or len(samples) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient samples for training: {len(samples) if samples else 0}"
            )
        
        # Convert to arrays (use original labels - should be clean)
        X, y = BaselineService._samples_to_arrays(samples)
        
        logger.info(f"📊 Training on {len(samples)} samples")
        
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=y if len(np.unique(y)) > 1 else None
        )
        
        logger.info(f"Split: {len(X_train)} train, {len(X_test)} test")
        
        # Get ML integration
        ml = get_ml_integration()
        
        # Set hyperparameters
        if hyperparameters is None:
            hyperparameters = BaselineService._get_default_hyperparameters(model_type)
        
        # Train model
        logger.info(f"Training {model_type}...")
        
        from ml_pipeline.src.data.model_trainer import get_model
        baseline_model = get_model(model_type, hyperparameters)
        
        # Time the training
        import time
        start_time = time.time()
        baseline_model.train(X_train, y_train)
        training_time = time.time() - start_time
        
        logger.info(f"✅ Training complete in {training_time:.2f}s")
        
        # Evaluate on both train and test sets
        y_train_pred = baseline_model.predict(X_train)
        y_test_pred = baseline_model.predict(X_test)
        
        train_metrics = ml.evaluate_model(X_train, y_train, y_train_pred)
        test_metrics = ml.evaluate_model(X_test, y_test, y_test_pred)
        
        logger.info(f"📊 Train Metrics:")
        logger.info(f"   Accuracy: {train_metrics['accuracy']:.4f}")
        logger.info(f"📊 Test Metrics:")
        logger.info(f"   Accuracy: {test_metrics['accuracy']:.4f}")
        logger.info(f"   Precision: {test_metrics['precision']:.4f}")
        logger.info(f"   Recall: {test_metrics['recall']:.4f}")
        logger.info(f"   F1-Score: {test_metrics['f1_score']:.4f}")
        
        # Save model to database
        model_display_name = f"{model_type.replace('_', ' ').title()} (Baseline)"
        
        baseline_model_db = MLModel(
            dataset_id=dataset_id,
            name=model_display_name,
            model_type=model_type,
            description=f"Baseline model trained on clean dataset",
            hyperparameters=json.dumps(hyperparameters),
            train_accuracy=train_metrics['accuracy'],
            test_accuracy=test_metrics['accuracy'],
            precision=test_metrics['precision'],
            recall=test_metrics['recall'],
            f1_score=test_metrics['f1_score'],
            num_samples_trained=len(X_train),
            training_time_seconds=training_time,
            is_baseline=True,
            is_active=True
        )
        
        db.add(baseline_model_db)
        db.commit()
        db.refresh(baseline_model_db)
        
        logger.info(f"✅ Saved baseline model: {baseline_model_db.name} (ID: {baseline_model_db.id})")
        
        return {
            "dataset_id": dataset_id,
            "model_id": baseline_model_db.id,
            "model_type": model_type,
            "model_name": model_display_name,
            "hyperparameters": hyperparameters,
            "train_metrics": {
                "accuracy": train_metrics['accuracy'],
                "precision": train_metrics['precision'],
                "recall": train_metrics['recall'],
                "f1_score": train_metrics['f1_score']
            },
            "test_metrics": {
                "accuracy": test_metrics['accuracy'],
                "precision": test_metrics['precision'],
                "recall": test_metrics['recall'],
                "f1_score": test_metrics['f1_score']
            },
            "training_info": {
                "samples_trained": len(X_train),
                "samples_tested": len(X_test),
                "training_time_seconds": round(training_time, 2)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _samples_to_arrays(samples: list) -> Tuple[np.ndarray, np.ndarray]:
        """Convert samples to numpy arrays using current_label"""
        features = []
        labels = []
        
        for sample in samples:
            feat = json.loads(sample.features)
            features.append(feat)
            labels.append(sample.current_label)  # Use current_label
        
        return np.array(features), np.array(labels)
    
    @staticmethod
    def _get_default_hyperparameters(model_type: str) -> Dict[str, Any]:
        """Get default hyperparameters for each model type"""
        defaults = {
            "random_forest": {
                "n_estimators": 100,
                "max_depth": None,
                "random_state": 42,
                "n_jobs": -1
            },
            "logistic": {
                "max_iter": 1000,
                "random_state": 42,
                "n_jobs": -1
            },
            "svm": {
                "kernel": "rbf",
                "random_state": 42
            }
        }
        
        return defaults.get(model_type, {})