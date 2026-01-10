"""
Dataset service - Business logic for dataset operations
"""
from sqlalchemy.orm import Session
from models.dataset import Dataset, Sample
from fastapi import UploadFile, HTTPException
import pandas as pd
import json
import os
from typing import List, Dict, Any
from datetime import datetime


class DatasetService:
    """Service class for dataset operations"""
    
    @staticmethod
    def get_all_datasets(db: Session, skip: int = 0, limit: int = 100) -> List[Dataset]:
        """Get all active datasets"""
        return db.query(Dataset).filter(
            Dataset.is_active == True
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_dataset_by_id(db: Session, dataset_id: int) -> Dataset:
        """Get dataset by ID"""
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.is_active == True
        ).first()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        return dataset
    
    @staticmethod
    async def upload_csv_dataset(
        db: Session,
        file: UploadFile,
        name: str,
        description: str = None
    ) -> Dataset:
        """
        Upload and process CSV dataset
        
        Expected CSV format:
        - Last column should be the label/target
        - All other columns are features
        - First row should be headers
        """
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are supported"
            )
        
        # Check if dataset name already exists
        existing = db.query(Dataset).filter(Dataset.name == name).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset with name '{name}' already exists"
            )
        
        try:
            # Read CSV file
            contents = await file.read()
            
            # Save file temporarily
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(upload_dir, safe_filename)
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Parse CSV
            df = pd.read_csv(file_path)
            
            if df.empty:
                raise HTTPException(status_code=400, detail="CSV file is empty")
            
            # Assume last column is the label
            feature_columns = df.columns[:-1].tolist()
            label_column = df.columns[-1]
            
            # Get dataset info
            num_samples = len(df)
            num_features = len(feature_columns)
            num_classes = df[label_column].nunique()
            
            # Create dataset entry
            dataset = Dataset(
                name=name,
                description=description or f"Uploaded CSV dataset with {num_samples} samples",
                file_path=file_path,
                num_samples=num_samples,
                num_features=num_features,
                num_classes=num_classes
            )
            
            db.add(dataset)
            db.commit()
            db.refresh(dataset)
            
            # Create sample entries
            samples_created = 0
            for idx, row in df.iterrows():
                features = row[feature_columns].tolist()
                label = int(row[label_column])
                
                sample = Sample(
                    dataset_id=dataset.id,
                    sample_index=int(idx),
                    features=json.dumps(features),
                    original_label=label,
                    current_label=label,
                    is_suspicious=False,
                    is_corrected=False
                )
                
                db.add(sample)
                samples_created += 1
                
                # Commit in batches
                if samples_created % 100 == 0:
                    db.commit()
            
            db.commit()
            
            return dataset
            
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="CSV file is empty or invalid")
        except Exception as e:
            db.rollback()
            # Clean up file if dataset creation failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Error processing dataset: {str(e)}")
    
    @staticmethod
    def delete_dataset(db: Session, dataset_id: int) -> bool:
        """Soft delete a dataset"""
        dataset = DatasetService.get_dataset_by_id(db, dataset_id)
        dataset.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def get_dataset_stats(db: Session, dataset_id: int) -> Dict[str, Any]:
        """Get comprehensive dataset statistics"""
        dataset = DatasetService.get_dataset_by_id(db, dataset_id)
        
        total_samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id
        ).count()
        
        suspicious_samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id,
            Sample.is_suspicious == True
        ).count()
        
        corrected_samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id,
            Sample.is_corrected == True
        ).count()
        
        # Count mismatched labels
        mismatched = db.query(Sample).filter(
            Sample.dataset_id == dataset_id,
            Sample.original_label != Sample.current_label
        ).count()
        
        return {
            "dataset_id": dataset_id,
            "name": dataset.name,
            "total_samples": total_samples,
            "num_features": dataset.num_features,
            "num_classes": dataset.num_classes,
            "suspicious_samples": suspicious_samples,
            "corrected_samples": corrected_samples,
            "mismatched_labels": mismatched,
            "noise_percentage": round((mismatched / total_samples * 100) if total_samples > 0 else 0, 2)
        }