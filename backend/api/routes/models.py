from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from schemas.model import (
    MLModelCreate, 
    MLModelResponse, 
    ModelIterationResponse,
    ModelComparisonResponse
)
from services.model_service import ModelService

router = APIRouter()


@router.get("/", response_model=List[MLModelResponse])
async def get_models(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all models, optionally filtered by dataset"""
    models = ModelService.get_all_models(db, dataset_id, skip, limit)
    return models


@router.get("/{model_id}", response_model=MLModelResponse)
async def get_model(model_id: int, db: Session = Depends(get_db)):
    """Get a specific model by ID"""
    model = ModelService.get_model_by_id(db, model_id)
    return model


@router.post("/", response_model=MLModelResponse, status_code=201)
async def create_model(
    model: MLModelCreate,
    db: Session = Depends(get_db)
):
    """Create a new model entry"""
    new_model = ModelService.create_model(
        db,
        dataset_id=model.dataset_id,
        name=model.name,
        model_type=model.model_type,
        description=model.description,
        hyperparameters=model.hyperparameters
    )
    return new_model


@router.get("/{model_id}/iterations", response_model=List[ModelIterationResponse])
async def get_model_iterations(model_id: int, db: Session = Depends(get_db)):
    """Get all training iterations for a model"""
    iterations = ModelService.get_model_iterations(db, model_id)
    return iterations


@router.get("/dataset/{dataset_id}/compare", response_model=List[ModelComparisonResponse])
async def compare_models(dataset_id: int, db: Session = Depends(get_db)):
    """Compare all models for a dataset"""
    comparison = ModelService.compare_models(db, dataset_id)
    return comparison


@router.delete("/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db)):
    """Soft delete a model"""
    ModelService.delete_model(db, model_id)
    return {"message": "Model deleted successfully"}