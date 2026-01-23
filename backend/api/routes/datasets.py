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
    label_column: Optional[str] = Form(None),  
    db: Session = Depends(get_db)
):
    """
    Upload a CSV dataset
    
    UPDATED: Now supports automatic label column detection and manual specification
    
    Expected CSV format:
    - Headers in first row
    - One column contains labels (will be auto-detected or can be specified)
    - All other columns are features
    
    Label Column Detection:
    - If label_column='auto' or None: Auto-detects 'class', 'label', 'target', or uses last column
    - If label_column='last': Uses last column
    - If label_column='first': Uses first column  
    - If label_column='column_name': Uses specified column name
    
    Args:
        file: CSV file to upload
        name: Dataset name (required)
        description: Dataset description (optional)
        label_column: Label column specification (optional, defaults to auto-detection)
    """
    # MODIFIED: Pass label_column parameter to service
    dataset = await DatasetService.upload_csv_dataset(
        db, 
        file, 
        name, 
        description,
        label_column=label_column  # ADDED
    )
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