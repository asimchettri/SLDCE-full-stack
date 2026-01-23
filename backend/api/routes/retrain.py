"""
Retrain API routes
Retrain models on corrected data and evaluate improvements
"""
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from core.database import get_db
from services.retrain_service import RetrainService
from schemas.retrain import (
    RetrainResponse,
    ModelComparisonResponse
)

router = APIRouter()


@router.post("/retrain/{dataset_id}", response_model=RetrainResponse)
async def retrain_model(
    dataset_id: int = Path(..., description="Dataset ID"),
    iteration: int = Query(1, description="Iteration number"),
    test_size: float = Query(0.2, ge=0.1, le=0.5, description="Test split ratio"),
    db: Session = Depends(get_db)
):
    """
    Retrain model on corrected dataset and evaluate improvement
    
    Complete retraining workflow:
    1. Loads samples with corrected labels
    2. Splits into train/test sets
    3. Trains new model
    4. Evaluates performance
    5. Compares with baseline model
    6. Saves new model to database
    7. Records iteration metrics
    
    Returns:
    - Baseline vs retrained metrics
    - Improvement statistics
    - Training information
    """
    result = RetrainService.retrain_and_evaluate(
        db,
        dataset_id=dataset_id,
        iteration=iteration,
        test_size=test_size
    )
    return result


@router.get("/compare/{dataset_id}", response_model=ModelComparisonResponse)
async def compare_models(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db)
):
    """
    Compare all models for a dataset
    
    Shows progression from baseline through all iterations.
    Includes:
    - Model metrics (accuracy, precision, recall, F1)
    - Training information
    - Samples corrected per iteration
    - Noise reduction statistics
    - Overall improvement
    """
    comparison = RetrainService.compare_all_models(db, dataset_id)
    return comparison