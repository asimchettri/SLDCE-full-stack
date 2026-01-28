"""
Retrain service - Retrain model on corrected dataset and evaluate improvement
CRITICAL: Measures the impact of corrections on model performance
"""
from sqlalchemy.orm import Session
from models.dataset import Sample
from models.model import MLModel, ModelIteration
from fastapi import HTTPException
from typing import Dict, Any, Tuple
import numpy as np
import json
import logging
from datetime import datetime

from services.ml_integration import get_ml_integration

logger = logging.getLogger(__name__)


class RetrainService:
    """Service for retraining models after corrections"""
    
    @staticmethod
    def retrain_and_evaluate(
        db: Session,
        dataset_id: int,
        iteration: int = 1,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Retrain model on corrected dataset and compare with baseline
        
        Workflow (following Dev 1's Notebook 09):
        1. Get all samples with corrected labels
        2. Split into train/test
        3. Train new model on corrected data
        4. Evaluate and compare with baseline
        5. Save new model to database
        6. Record iteration metrics
        
        Args:
            db: Database session
            dataset_id: Dataset ID
            iteration: Iteration number (default: 1)
            test_size: Test split ratio (default: 0.2)
            
        Returns:
            Comparison metrics and improvement statistics
        """
        logger.info(f"🔄 Retraining model on dataset {dataset_id}, iteration {iteration}")
        
        # Get all samples (with corrected labels)
        samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id
        ).all()
        
        if not samples or len(samples) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient samples for retraining: {len(samples) if samples else 0}"
            )
        
        # Convert to arrays
        X, y = RetrainService._samples_to_arrays(samples, use_current_labels=True)
        
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=y if len(np.unique(y)) > 1 else None
        )
        
        logger.info(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples")
        
        # Get ML integration
        ml = get_ml_integration()
        
        # Get model config
        model_name = ml.config.get("model", {}).get("name", "random_forest")
        model_params = ml.config.get("model", {}).get("params", {
            "n_estimators": 100,
            "random_state": 42,
            "n_jobs": -1
        })
        
        # Train new model on corrected data
        logger.info(f"Training {model_name} on corrected dataset...")
        
        from ml_pipeline.src.data.model_trainer import get_model
        retrained_model = get_model(model_name, model_params)
        
        # Time the training
        import time
        start_time = time.time()
        retrained_model.train(X_train, y_train)
        training_time = time.time() - start_time
        
        logger.info(f"✅ Training complete in {training_time:.2f}s")
        
        # Evaluate on test set
        y_pred = retrained_model.predict(X_test)
        metrics = ml.evaluate_model(X_test, y_test, y_pred)
        
        logger.info(f"📊 Test Metrics:")
        logger.info(f"   Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"   Precision: {metrics['precision']:.4f}")
        logger.info(f"   Recall: {metrics['recall']:.4f}")
        logger.info(f"   F1-Score: {metrics['f1_score']:.4f}")
        
        # Get baseline model for comparison
        baseline_model = db.query(MLModel).filter(
            MLModel.dataset_id == dataset_id,
            MLModel.is_baseline == True,
            MLModel.is_active == True
        ).first()
        
        # Calculate improvement
        if baseline_model:
            # Try test_accuracy first, then train_accuracy, then calculate it
            if baseline_model.test_accuracy and baseline_model.test_accuracy > 0:
                baseline_accuracy = baseline_model.test_accuracy
            elif baseline_model.train_accuracy and baseline_model.train_accuracy > 0:
                baseline_accuracy = baseline_model.train_accuracy
            else:
                # Baseline exists but no metrics - this shouldn't happen
                logger.warning("Baseline model has no stored metrics!")
                baseline_accuracy = 0.0
        else:
            logger.warning("No baseline model found!")
            baseline_accuracy = 0.0

    # Also get baseline's other metrics for comparison
        baseline_precision = baseline_model.precision if baseline_model else 0.0
        baseline_recall = baseline_model.recall if baseline_model else 0.0
        baseline_f1 = baseline_model.f1_score if baseline_model else 0.0
        improvement = metrics['accuracy'] - baseline_accuracy
        improvement_pct = (improvement / baseline_accuracy * 100) if baseline_accuracy > 0 else 0
        
        logger.info(f"📈 Improvement over baseline:")
        logger.info(f"   Baseline: {baseline_accuracy:.4f}")
        logger.info(f"   After corrections: {metrics['accuracy']:.4f}")
        logger.info(f"   Improvement: {improvement:+.4f} ({improvement_pct:+.2f}%)")
        
        # Create new model entry for retrained model
        retrained_model_db = MLModel(
            dataset_id=dataset_id,
            name=f"{model_name.replace('_', ' ').title()} (Iteration {iteration})",
            model_type=model_name,
            description=f"Model retrained after applying corrections (iteration {iteration})",
            hyperparameters=json.dumps(model_params),
            train_accuracy=None,  # Could calculate if needed
            test_accuracy=metrics['accuracy'],
            precision=metrics['precision'],
            recall=metrics['recall'],
            f1_score=metrics['f1_score'],
            num_samples_trained=len(X_train),
            training_time_seconds=training_time,
            is_baseline=False,
            is_active=True
        )
        
        db.add(retrained_model_db)
        db.commit()
        db.refresh(retrained_model_db)
        
        logger.info(f"✅ Saved retrained model: {retrained_model_db.name} (ID: {retrained_model_db.id})")
        
        # Record iteration metrics
        samples_corrected = db.query(Sample).filter(
            Sample.dataset_id == dataset_id,
            Sample.is_corrected == True
        ).count()
        
        labels_changed = db.query(Sample).filter(
            Sample.dataset_id == dataset_id,
            Sample.original_label != Sample.current_label
        ).count()
        
        noise_reduced = (labels_changed / len(samples) * 100) if len(samples) > 0 else 0
        
        iteration_record = ModelIteration(
            model_id=retrained_model_db.id,
            dataset_id=dataset_id,
            iteration_number=iteration,
            accuracy=metrics['accuracy'],
            precision=metrics['precision'],
            recall=metrics['recall'],
            f1_score=metrics['f1_score'],
            samples_corrected=samples_corrected,
            noise_reduced=noise_reduced
        )
        
        db.add(iteration_record)
        db.commit()
        db.refresh(iteration_record)
        
        return {
            "dataset_id": dataset_id,
            "iteration": iteration,
            "baseline_model_id": baseline_model.id if baseline_model else None,
            "retrained_model_id": retrained_model_db.id,
            "baseline_metrics": {
                "accuracy": baseline_accuracy,
                "precision": baseline_precision,  
                "recall": baseline_recall,        
                "f1_score": baseline_f1,          
                "test_accuracy": baseline_model.test_accuracy if baseline_model else None
            },
            "retrained_metrics": {
                "accuracy": metrics['accuracy'],
                "precision": metrics['precision'],
                "recall": metrics['recall'],
                "f1_score": metrics['f1_score']
            },
            "improvement": {
                "absolute": round(improvement, 4),
                "percentage": round(improvement_pct, 2)
            },
            "training_info": {
                "samples_trained": len(X_train),
                "samples_tested": len(X_test),
                "training_time_seconds": round(training_time, 2),
                "samples_corrected": samples_corrected,
                "labels_changed": labels_changed,
                "noise_reduced_pct": round(noise_reduced, 2)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _samples_to_arrays(
        samples: list,
        use_current_labels: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert samples to numpy arrays
        
        Args:
            samples: List of Sample objects
            use_current_labels: If True, use current_label (corrected).
                              If False, use original_label.
        
        Returns:
            (X, y) tuple
        """
        features = []
        labels = []
        
        for sample in samples:
            # Parse features
            feat = json.loads(sample.features)
            features.append(feat)
            
            # Choose label source
            label = sample.current_label if use_current_labels else sample.original_label
            labels.append(label)
        
        return np.array(features), np.array(labels)
    
    @staticmethod
    def compare_all_models(
        db: Session,
        dataset_id: int
    ) -> Dict[str, Any]:
        """
        Compare all models for a dataset
        
        Shows progression from baseline through iterations
        """
        models = db.query(MLModel).filter(
            MLModel.dataset_id == dataset_id,
            MLModel.is_active == True
        ).order_by(MLModel.created_at).all()
        
        if not models:
            raise HTTPException(
                status_code=404,
                detail=f"No models found for dataset {dataset_id}"
            )
        
        comparison = []
        for model in models:
            # Get iteration data if available
            iteration = db.query(ModelIteration).filter(
                ModelIteration.model_id == model.id
            ).first()
            
            comparison.append({
                "model_id": model.id,
                "name": model.name,
                "model_type": model.model_type,
                "is_baseline": model.is_baseline,
                "accuracy": model.test_accuracy or model.train_accuracy or 0,
                "precision": model.precision,
                "recall": model.recall,
                "f1_score": model.f1_score,
                "training_time": model.training_time_seconds,
                "samples_trained": model.num_samples_trained,
                "iteration_number": iteration.iteration_number if iteration else None,
                "samples_corrected": iteration.samples_corrected if iteration else None,
                "noise_reduced": iteration.noise_reduced if iteration else None,
                "created_at": model.created_at.isoformat() if model.created_at else None
            })
        
        # Calculate overall improvement
        baseline = next((m for m in comparison if m['is_baseline']), None)
        latest = comparison[-1] if comparison else None
        
        improvement = None
        if baseline and latest and not latest['is_baseline']:
            baseline_acc = baseline['accuracy']
            latest_acc = latest['accuracy']
            improvement = {
                "absolute": round(latest_acc - baseline_acc, 4),
                "percentage": round(
                    ((latest_acc - baseline_acc) / baseline_acc * 100) if baseline_acc > 0 else 0,
                    2
                )
            }
        
        return {
            "dataset_id": dataset_id,
            "total_models": len(comparison),
            "models": comparison,
            "overall_improvement": improvement
        }