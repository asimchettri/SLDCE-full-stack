from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from models.dataset import Sample
from schemas.dataset import SampleResponse
import json

router = APIRouter()


@router.get("/", response_model=List[SampleResponse])
async def get_samples(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    is_suspicious: Optional[bool] = Query(None, description="Filter by suspicious flag"),
    is_corrected: Optional[bool] = Query(None, description="Filter by corrected flag"),
    limit: int = Query(100, ge=1, le=1000, description="Max samples to return"),
    offset: int = Query(0, ge=0, description="Number of samples to skip"),
    db: Session = Depends(get_db)
):
    """Get samples with optional filters"""
    query = db.query(Sample)
    
    if dataset_id is not None:
        query = query.filter(Sample.dataset_id == dataset_id)
    if is_suspicious is not None:
        query = query.filter(Sample.is_suspicious == is_suspicious)
    if is_corrected is not None:
        query = query.filter(Sample.is_corrected == is_corrected)
    
    samples = query.offset(offset).limit(limit).all()
    return samples


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample(sample_id: int, db: Session = Depends(get_db)):
    """Get a specific sample by ID"""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample


@router.get("/{sample_id}/features")
async def get_sample_features(sample_id: int, db: Session = Depends(get_db)):
    """Get sample features as parsed JSON"""
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    return {
        "sample_id": sample.id,
        "features": json.loads(sample.features),
        "current_label": sample.current_label,
        "original_label": sample.original_label
    }


@router.get("/dataset/{dataset_id}/stats")
async def get_dataset_stats(dataset_id: int, db: Session = Depends(get_db)):
    """Get statistics for a dataset"""
    total = db.query(Sample).filter(Sample.dataset_id == dataset_id).count()
    suspicious = db.query(Sample).filter(
        Sample.dataset_id == dataset_id,
        Sample.is_suspicious == True
    ).count()
    corrected = db.query(Sample).filter(
        Sample.dataset_id == dataset_id,
        Sample.is_corrected == True
    ).count()
    
    # Count label mismatches (noisy labels)
    mismatches = db.query(Sample).filter(
        Sample.dataset_id == dataset_id,
        Sample.original_label != Sample.current_label
    ).count()
    
    return {
        "dataset_id": dataset_id,
        "total_samples": total,
        "suspicious_samples": suspicious,
        "corrected_samples": corrected,
        "noisy_labels": mismatches,
        "noise_percentage": round((mismatches / total * 100) if total > 0 else 0, 2)
    }