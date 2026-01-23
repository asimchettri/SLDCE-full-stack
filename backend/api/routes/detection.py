from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from schemas.detection import (
    DetectionRunRequest,
    DetectionRunResponse,
    DetectionResponse,
    SuggestionGenerateResponse,
    DetectionStatsResponse,
    SignalStatsResponse
)

from services.detection_service import DetectionService
from services.suggestion_service import SuggestionService

router = APIRouter()


@router.post("/run", response_model=DetectionRunResponse)
async def run_detection(
    request: DetectionRunRequest,
    db: Session = Depends(get_db)
):
    """
    Run detection on a dataset to identify suspicious samples
    
    Supports configurable signal weights for priority calculation.
    Example weights: {"confidence": 0.6, "anomaly": 0.4}
    """
    result = DetectionService.run_detection(
        db,
        dataset_id=request.dataset_id,
        confidence_threshold=request.confidence_threshold,
        max_samples=request.max_samples,
        priority_weights=request.priority_weights
    )
    return result


@router.post("/suggestions", response_model=SuggestionGenerateResponse)
async def generate_suggestions(
    dataset_id: int = Query(..., description="Dataset ID"),
    iteration: int = Query(1, description="Iteration number"),
    db: Session = Depends(get_db)
):
    """Generate correction suggestions for detected samples"""
    result = SuggestionService.generate_suggestions(db, dataset_id, iteration)
    return result


@router.get("/stats/{dataset_id}", response_model=DetectionStatsResponse)
async def get_detection_stats(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """Get detection statistics for a dataset"""
    stats = DetectionService.get_detection_stats(db, dataset_id)
    return stats


@router.get("/list", response_model=List[DetectionResponse])
async def get_detections(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    iteration: Optional[int] = Query(None, description="Filter by iteration"),
    min_priority: Optional[float] = Query(None, description="Minimum priority score"),
    min_confidence: Optional[float] = Query(None, description="Minimum confidence score"),
    min_anomaly: Optional[float] = Query(None, description="Minimum anomaly score"),
    signal_type: Optional[str] = Query(None, description="Filter by dominant signal: confidence, anomaly, both"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get detections with optional filters including signal-specific filters"""
    detections = DetectionService.get_detections(
        db,
        dataset_id=dataset_id,
        iteration=iteration,
        min_priority=min_priority,
        min_confidence=min_confidence,
        min_anomaly=min_anomaly,
        signal_type=signal_type,
        limit=limit,
        offset=offset
    )
    return detections


@router.get("/{detection_id}")
async def get_detection_details(
    detection_id: int,
    db: Session = Depends(get_db)
):
    """Get detection with sample details"""
    result = DetectionService.get_detection_with_sample(db, detection_id)
    return result


@router.get("/signal-stats/{dataset_id}", response_model=SignalStatsResponse)
async def get_signal_stats(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """Get signal-specific statistics for a dataset"""
    stats = DetectionService.get_signal_stats(db, dataset_id)
    return stats