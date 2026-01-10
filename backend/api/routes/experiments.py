from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentIterationResponse,
    ExperimentSummary
)
from services.experiment_service import ExperimentService

router = APIRouter()


@router.get("/", response_model=List[ExperimentResponse])
async def get_experiments(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all experiments, optionally filtered by dataset"""
    experiments = ExperimentService.get_all_experiments(db, dataset_id, skip, limit)
    return experiments


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """Get a specific experiment by ID"""
    experiment = ExperimentService.get_experiment_by_id(db, experiment_id)
    return experiment


@router.post("/", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    experiment: ExperimentCreate,
    db: Session = Depends(get_db)
):
    """Create a new experiment"""
    new_experiment = ExperimentService.create_experiment(
        db,
        dataset_id=experiment.dataset_id,
        name=experiment.name,
        noise_percentage=experiment.noise_percentage,
        description=experiment.description,
        detection_threshold=experiment.detection_threshold,
        max_iterations=experiment.max_iterations
    )
    return new_experiment


@router.get("/{experiment_id}/iterations", response_model=List[ExperimentIterationResponse])
async def get_experiment_iterations(experiment_id: int, db: Session = Depends(get_db)):
    """Get all iterations for an experiment"""
    iterations = ExperimentService.get_experiment_iterations(db, experiment_id)
    return iterations


@router.get("/{experiment_id}/summary", response_model=ExperimentSummary)
async def get_experiment_summary(experiment_id: int, db: Session = Depends(get_db)):
    """Get experiment summary statistics"""
    summary = ExperimentService.get_experiment_summary(db, experiment_id)
    return summary


@router.post("/{experiment_id}/complete", response_model=ExperimentResponse)
async def complete_experiment(
    experiment_id: int,
    total_time_seconds: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Mark an experiment as completed"""
    experiment = ExperimentService.complete_experiment(db, experiment_id, total_time_seconds)
    return experiment