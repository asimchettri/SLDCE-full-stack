"""
Baseline training API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from core.database import get_db
from services.baseline_service import BaselineService

router = APIRouter()


class BaselineTrainRequest(BaseModel):
    """Request to train baseline model"""
    dataset_id: int
    model_type: str = Field(
        default="random_forest",
        pattern="^(random_forest|logistic|svm)$",
        description="Model type: random_forest, logistic, or svm"
    )
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    hyperparameters: Optional[Dict[str, Any]] = None


@router.post("/train")
async def train_baseline(
    request: BaselineTrainRequest,
    db: Session = Depends(get_db)
):
    """
    Train baseline model on clean dataset
    
    This should be done BEFORE injecting noise or running detection.
    Establishes ground truth performance on clean data.
    
    Supported models:
    - random_forest: Random Forest Classifier
    - logistic: Logistic Regression
    - svm: Support Vector Machine
    
    Example:
```json
    {
        "dataset_id": 1,
        "model_type": "random_forest",
        "test_size": 0.2,
        "hyperparameters": {
            "n_estimators": 200,
            "max_depth": 10
        }
    }
```
    """
    try:
        result = BaselineService.train_baseline(
            db=db,
            dataset_id=request.dataset_id,
            model_type=request.model_type,
            test_size=request.test_size,
            hyperparameters=request.hyperparameters
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Baseline training failed: {str(e)}"
        )


@router.get("/check/{dataset_id}")
async def check_baseline_exists(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """Check if baseline model exists for a dataset"""
    from models.model import MLModel
    
    baseline = db.query(MLModel).filter(
        MLModel.dataset_id == dataset_id,
        MLModel.is_baseline == True,
        MLModel.is_active == True
    ).first()
    
    if baseline:
        return {
            "exists": True,
            "model_id": baseline.id,
            "model_type": baseline.model_type,
            "model_name": baseline.name,
            "test_accuracy": baseline.test_accuracy,
            "created_at": baseline.created_at.isoformat() if baseline.created_at else None
        }
    else:
        return {
            "exists": False
        }