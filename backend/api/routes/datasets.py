from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from schemas.dataset import DatasetCreate, DatasetResponse
from services.dataset_service import DatasetService

router = APIRouter()


@router.get("/", response_model=List[DatasetResponse])
async def get_datasets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all datasets"""
    datasets = DatasetService.get_all_datasets(db, skip, limit)
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Get a specific dataset by ID"""
    dataset = DatasetService.get_dataset_by_id(db, dataset_id)
    return dataset


@router.post("/upload", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a CSV dataset
    
    Expected CSV format:
    - Headers in first row
    - Features in all columns except last
    - Labels in last column
    """
    dataset = await DatasetService.upload_csv_dataset(db, file, name, description)
    return dataset


@router.get("/{dataset_id}/stats")
async def get_dataset_stats(dataset_id: int, db: Session = Depends(get_db)):
    """Get comprehensive dataset statistics"""
    stats = DatasetService.get_dataset_stats(db, dataset_id)
    return stats


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Soft delete a dataset"""
    DatasetService.delete_dataset(db, dataset_id)
    return {"message": "Dataset deleted successfully"}