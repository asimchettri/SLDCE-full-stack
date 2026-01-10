"""
Model service - Business logic for ML model operations
"""
from sqlalchemy.orm import Session
from models.model import MLModel, ModelIteration
from fastapi import HTTPException
from typing import List, Dict, Any


class ModelService:
    """Service class for model operations"""
    
    @staticmethod
    def get_all_models(db: Session, dataset_id: int = None, skip: int = 0, limit: int = 100) -> List[MLModel]:
        """Get all active models, optionally filtered by dataset"""
        query = db.query(MLModel).filter(MLModel.is_active == True)
        
        if dataset_id:
            query = query.filter(MLModel.dataset_id == dataset_id)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_model_by_id(db: Session, model_id: int) -> MLModel:
        """Get model by ID"""
        model = db.query(MLModel).filter(
            MLModel.id == model_id,
            MLModel.is_active == True
        ).first()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return model
    
    @staticmethod
    def create_model(
        db: Session,
        dataset_id: int,
        name: str,
        model_type: str,
        description: str = None,
        hyperparameters: Dict[str, Any] = None
    ) -> MLModel:
        """Create a new model entry"""
        # Check if model with same name exists for this dataset
        existing = db.query(MLModel).filter(
            MLModel.dataset_id == dataset_id,
            MLModel.name == name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Model with name '{name}' already exists for this dataset"
            )
        
        model = MLModel(
            dataset_id=dataset_id,
            name=name,
            model_type=model_type,
            description=description,
            hyperparameters=hyperparameters
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        return model
    
    @staticmethod
    def update_model_metrics(
        db: Session,
        model_id: int,
        train_accuracy: float = None,
        test_accuracy: float = None,
        precision: float = None,
        recall: float = None,
        f1_score: float = None,
        num_samples_trained: int = None,
        training_time_seconds: float = None
    ) -> MLModel:
        """Update model performance metrics"""
        model = ModelService.get_model_by_id(db, model_id)
        
        if train_accuracy is not None:
            model.train_accuracy = train_accuracy
        if test_accuracy is not None:
            model.test_accuracy = test_accuracy
        if precision is not None:
            model.precision = precision
        if recall is not None:
            model.recall = recall
        if f1_score is not None:
            model.f1_score = f1_score
        if num_samples_trained is not None:
            model.num_samples_trained = num_samples_trained
        if training_time_seconds is not None:
            model.training_time_seconds = training_time_seconds
        
        db.commit()
        db.refresh(model)
        
        return model
    
    @staticmethod
    def get_model_iterations(db: Session, model_id: int) -> List[ModelIteration]:
        """Get all iterations for a model"""
        return db.query(ModelIteration).filter(
            ModelIteration.model_id == model_id
        ).order_by(ModelIteration.iteration_number).all()
    
    @staticmethod
    def add_iteration(
        db: Session,
        model_id: int,
        dataset_id: int,
        iteration_number: int,
        accuracy: float,
        precision: float = None,
        recall: float = None,
        f1_score: float = None,
        samples_corrected: int = 0,
        noise_reduced: float = 0.0
    ) -> ModelIteration:
        """Add a new training iteration"""
        iteration = ModelIteration(
            model_id=model_id,
            dataset_id=dataset_id,
            iteration_number=iteration_number,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            samples_corrected=samples_corrected,
            noise_reduced=noise_reduced
        )
        
        db.add(iteration)
        db.commit()
        db.refresh(iteration)
        
        return iteration
    
    @staticmethod
    def compare_models(db: Session, dataset_id: int) -> List[Dict[str, Any]]:
        """Compare all models for a dataset"""
        models = db.query(MLModel).filter(
            MLModel.dataset_id == dataset_id,
            MLModel.is_active == True
        ).all()
        
        comparison = []
        for model in models:
            comparison.append({
                "model_id": model.id,
                "name": model.name,
                "model_type": model.model_type,
                "accuracy": model.test_accuracy or model.train_accuracy or 0,
                "precision": model.precision,
                "recall": model.recall,
                "f1_score": model.f1_score,
                "training_time": model.training_time_seconds,
                "is_baseline": model.is_baseline
            })
        
        # Sort by accuracy descending
        comparison.sort(key=lambda x: x["accuracy"], reverse=True)
        
        return comparison
    
    @staticmethod
    def delete_model(db: Session, model_id: int) -> bool:
        """Soft delete a model"""
        model = ModelService.get_model_by_id(db, model_id)
        model.is_active = False
        db.commit()
        return True