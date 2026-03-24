"""
Dataset service - Business logic for dataset operations
ENHANCED: Handles both numeric and string labels with automatic conversion
"""
from sqlalchemy.orm import Session
from models.dataset import Dataset, Sample
from fastapi import UploadFile, HTTPException
import pandas as pd
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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
        Detect which column contains the labels
        
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
        common_label_names = ['class', 'label', 'target', 'y', 'income', 'output']
        columns_lower = {col.lower(): col for col in columns}
        
        for label_name in common_label_names:
            if label_name in columns_lower:
                detected_col = columns_lower[label_name]
                logger.info(f"✅ Auto-detected label column: '{detected_col}'")
                return detected_col
        
        # Priority 3: Default to last column
        logger.warning(f"⚠️  No standard label column found. Using last column: '{columns[-1]}'")
        return columns[-1]
    
    @staticmethod
    def _encode_string_labels(
        df: pd.DataFrame, 
        label_column: str
    ) -> Tuple[pd.DataFrame, Optional[Dict[str, int]]]:
        """
        Convert string labels to integers if needed
        
        Args:
            df: DataFrame with labels
            label_column: Name of label column
            
        Returns:
            (Modified DataFrame, Label mapping dict or None)
        """
        label_series = df[label_column]
        
        # Check if labels are strings
        if label_series.dtype == 'object' or pd.api.types.is_string_dtype(label_series):
            logger.info(f"📝 String labels detected in column '{label_column}'")
            
            # Get unique labels
            unique_labels = sorted(label_series.unique())
            
            # Create mapping: string -> integer
            label_mapping = {label: idx for idx, label in enumerate(unique_labels)}
            
            logger.info(f"📝 Label encoding mapping:")
            for original, encoded in label_mapping.items():
                logger.info(f"   '{original}' → {encoded}")
            
            # Apply mapping to create integer labels
            df[label_column] = label_series.map(label_mapping)
            
            return df, label_mapping
        
        # Labels are already numeric
        return df, None
    
    @staticmethod
    def _validate_labels(
        labels: pd.Series, 
        column_name: str,
        is_encoded: bool = False
    ) -> None:
        """
        Validate label column
        
        Checks:
        - Labels should be integers or can be converted to integers
        - Label values should be reasonable
        - Should have reasonable number of unique classes (2-100)
        
        Args:
            labels: Series of label values (should be numeric after encoding)
            column_name: Name of label column for error messages
            is_encoded: Whether labels were just encoded from strings
            
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
        
        # Check 2: Very large label values (only for non-encoded numeric labels)
        if not is_encoded:
            try:
                max_label = labels.max()
                if max_label > 1000:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Column '{column_name}' has very large values (max={max_label}). "
                               f"These look like feature values, not class labels. "
                               f"Expected labels: 0, 1, 2, etc. "
                               f"Please specify the correct label column."
                    )
            except (TypeError, ValueError):
                # Labels might be strings that we'll encode later
                pass
        
        # Check 3: Need at least 2 classes
        if num_classes < 2:
            raise HTTPException(
                status_code=400,
                detail=f"Column '{column_name}' has only {num_classes} unique value(s). "
                       f"Need at least 2 classes for classification."
            )
        
        logger.info(f"✅ Label validation passed: {num_classes} classes")
    
    @staticmethod
    async def upload_csv_dataset(
        db: Session,
        file: UploadFile,
        name: str,
        description: str = None,
        label_column: Optional[str] = None
    ) -> Dataset:
        """
        Upload and process CSV dataset
        ENHANCED: Automatically handles string labels by encoding them to integers
        
        Expected CSV format:
        - First row should be headers
        - One column should contain labels (auto-detected or specified)
        - All other columns are features
        - Labels can be strings (e.g., "<=50K", ">50K") or integers (0, 1, 2)
        
        Args:
            db: Database session
            file: Uploaded CSV file
            name: Dataset name
            description: Optional description
            label_column: Optional label column name ("auto", "last", "first", or column name)
            
        Returns:
            Created Dataset object
        """
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are supported"
            )
        
        # Check if dataset name already exists
        existing = db.query(Dataset).filter(
            Dataset.name == name,
            Dataset.is_active == True
        ).first()
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
            
            logger.info(f"📂 Loaded CSV: {len(df)} rows, {len(df.columns)} columns")
            
            # Step 1: Detect label column
            detected_label_col = DatasetService._detect_label_column(df, label_column)
            
            # Step 2: Encode string labels if needed
            df, label_mapping = DatasetService._encode_string_labels(df, detected_label_col)
            
            # Step 3: Validate labels (after encoding)
            DatasetService._validate_labels(
                df[detected_label_col], 
                detected_label_col,
                is_encoded=(label_mapping is not None)
            )
            
            # Step 4: Separate features and labels
            feature_columns = [col for col in df.columns if col != detected_label_col]
            label_column_name = detected_label_col
            
            # Get dataset info
            num_samples = len(df)
            num_features = len(feature_columns)
            num_classes = df[label_column_name].nunique()
            
            logger.info(f"📊 Dataset Info:")
            logger.info(f"   - Samples: {num_samples}")
            logger.info(f"   - Features: {num_features} ({', '.join(feature_columns[:3])}...)")
            logger.info(f"   - Label column: '{label_column_name}'")
            logger.info(f"   - Classes: {num_classes}")
            
            if label_mapping:
                logger.info(f"   - Label encoding applied: {list(label_mapping.keys())[:5]}...")
            
            
            
            
            # Create dataset entry
            dataset = Dataset(
                name=name,
                description=description or f"Uploaded CSV dataset with {num_samples} samples",
                file_path=file_path,
                num_samples=num_samples,
                num_features=num_features,
                num_classes=num_classes,
                feature_names=json.dumps(feature_columns),
                label_column_name=label_column_name,
                label_mapping=json.dumps(label_mapping) if label_mapping else None,  
            )
            
            db.add(dataset)
            db.commit()
            db.refresh(dataset)
            
            logger.info(f"✅ Dataset created: {dataset.name} (ID: {dataset.id})")
            
            # Step 5: Create sample entries — use flush not commit to keep single transaction
            samples_created = 0
            for idx, row in df.iterrows():
                try:
                    features = row[feature_columns].tolist()
                    label = int(row[label_column_name])

                    sample = Sample(
                        dataset_id=dataset.id,
                        sample_index=int(idx),
                        features=json.dumps(features),
                        original_label=label,
                        current_label=label,
                        is_suspicious=False,
                        is_corrected=False,
                    )
                    db.add(sample)
                    samples_created += 1

                    # Flush in batches for memory efficiency but keep single transaction
                    if samples_created % 500 == 0:
                        db.flush()
                        logger.info(f"   Flushed {samples_created}/{num_samples} samples...")

                except Exception as e:
                    db.rollback()
                    logger.error(f"Failed to process row {idx}: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to process sample at row {idx}: {str(e)}"
                    )

            # Single final commit for all samples
            db.commit()
            logger.info(f"✅ Successfully committed {samples_created} samples") 
            
            return dataset
        
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="CSV file is empty or invalid")
        except pd.errors.ParserError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse CSV file: {str(e)}"
            )
        except HTTPException:
            # Re-raise HTTP exceptions (validation errors)
            raise
        except Exception as e:
            db.rollback()
            # Clean up file if dataset creation failed
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Dataset upload failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing dataset: {str(e)}"
            )
    
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