"""
Dataset service - Business logic for dataset operations

"""
from sqlalchemy.orm import Session
from models.dataset import Dataset, Sample
from fastapi import UploadFile, HTTPException
import pandas as pd
import json
import os
from typing import List, Dict, Any, Optional
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
    def _detect_label_column(df: pd.DataFrame, user_specified: Optional[str] = None) -> str:
        """
                
        Args:
            df: DataFrame to analyze
            user_specified: Optional column name from user
            
        Returns:
            Name of the label column
            
        Raises:
            HTTPException: If specified column doesn't exist
        """
        columns = df.columns.tolist()
        
        # Priority 1: User specified
        if user_specified:
            if user_specified == "auto":
                pass  # Continue to auto-detection
            elif user_specified == "last":
                return columns[-1]
            elif user_specified == "first":
                return columns[0]
            elif user_specified in columns:
                return user_specified
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Specified label column '{user_specified}' not found. Available: {columns}"
                )
        
        # Priority 2: Look for common label column names (case-insensitive)
        common_label_names = ['class', 'label', 'target', 'y']
        columns_lower = {col.lower(): col for col in columns}
        
        for label_name in common_label_names:
            if label_name in columns_lower:
                detected_col = columns_lower[label_name]
                print(f"✅ Auto-detected label column: '{detected_col}'")
                return detected_col
        
        # Priority 3: Default to last column
        print(f"⚠️  No standard label column found. Using last column: '{columns[-1]}'")
        return columns[-1]
    
    @staticmethod
    def _validate_labels(labels: pd.Series, column_name: str) -> None:
        """
        
        Checks:
        - Labels should be integers or can be converted to integers
        - Label values should be small (< 1000 typically)
        - Should have reasonable number of unique classes (2-100)
        
        Args:
            labels: Series of label values
            column_name: Name of label column for error messages
            
        Raises:
            HTTPException: If labels look suspicious
        """
        unique_labels = labels.unique()
        num_classes = len(unique_labels)
        
        # Check 1: Too many unique values (likely a feature, not label)
        if num_classes > 100:
            raise HTTPException(
                status_code=400,
                detail=f"Column '{column_name}' has {num_classes} unique values. "
                       f"This seems too many for a label column. "
                       f"Please specify the correct label column."
            )
        
        # Check 2: Very large label values (likely feature values like proline)
        max_label = labels.max()
        if max_label > 1000:
            raise HTTPException(
                status_code=400,
                detail=f"Column '{column_name}' has very large values (max={max_label}). "
                       f"These look like feature values, not class labels. "
                       f"Expected labels: 0, 1, 2, etc. "
                       f"Please specify the correct label column."
            )
        
        # Check 3: Labels should be reasonably distributed
        if num_classes < 2:
            raise HTTPException(
                status_code=400,
                detail=f"Column '{column_name}' has only {num_classes} unique value(s). "
                       f"Need at least 2 classes for classification."
            )
        
        print(f"✅ Label validation passed: {num_classes} classes, range [{labels.min()}, {labels.max()}]")
    
    @staticmethod
    async def upload_csv_dataset(
        db: Session,
        file: UploadFile,
        name: str,
        description: str = None,
        label_column: Optional[str] = None 
    ) -> Dataset:
        """
        
        
        Expected CSV format:
        - First row should be headers
        - One column should contain labels (auto-detected or specified)
        - All other columns are features
        
        Args:
            db: Database session
            file: Uploaded CSV file
            name: Dataset name
            description: Optional description
            label_column: Optional label column name ("auto", "last", "first", or column name)
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
            
            detected_label_col = DatasetService._detect_label_column(df, label_column)
            
            
            DatasetService._validate_labels(df[detected_label_col], detected_label_col)
            
            
            feature_columns = [col for col in df.columns if col != detected_label_col]
            label_column_name = detected_label_col
            
            # Get dataset info
            num_samples = len(df)
            num_features = len(feature_columns)
            num_classes = df[label_column_name].nunique()
            
            print(f"📊 Dataset Info:")
            print(f"   - Samples: {num_samples}")
            print(f"   - Features: {num_features} ({', '.join(feature_columns[:3])}...)")
            print(f"   - Label column: '{label_column_name}'")
            print(f"   - Classes: {num_classes} (values: {sorted(df[label_column_name].unique())})")
            
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
            
            # Create sample entries with correct label column
            samples_created = 0
            for idx, row in df.iterrows():
                # Extract features (all columns except label)
                features = row[feature_columns].tolist()
                # Extract label from detected column
                label = int(row[label_column_name])
                
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
            
            print(f"✅ Successfully created {samples_created} samples")
            
            return dataset
            
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="CSV file is empty or invalid")
        except HTTPException:
            # Re-raise HTTP exceptions (validation errors)
            raise
        except Exception as e:
            db.rollback()
            # Clean up file if dataset creation failed
            if 'file_path' in locals() and os.path.exists(file_path):
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