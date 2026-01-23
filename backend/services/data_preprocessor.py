"""
Data Preprocessor - Ensures consistency between database and ML pipeline
"""
import pandas as pd
import numpy as np
import json
from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from models.dataset import Sample, Dataset
import logging

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Handles data transformation between database format and ML pipeline format
    Ensures Dev 1's ML code receives data in the expected format
    """
    
    @staticmethod
    def samples_to_dataframe(samples: List[Sample]) -> pd.DataFrame:
        """
        Convert Sample objects to DataFrame (compatible with Dev 1's notebooks)
        
        Args:
            samples: List of Sample SQLAlchemy objects
            
        Returns:
            DataFrame with features as separate columns
        """
        data = []
        
        for sample in samples:
            # Parse JSON features
            try:
                features = json.loads(sample.features)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse features for sample {sample.id}: {e}")
                continue
            
            row = {
                'sample_id': sample.id,
                'sample_index': sample.sample_index,
                'current_label': sample.current_label,
                'original_label': sample.original_label,
            }
            
            # Add features as separate columns
            if isinstance(features, list):
                for i, value in enumerate(features):
                    row[f'feature_{i}'] = value
            elif isinstance(features, dict):
                # Handle dict-formatted features
                for key, value in features.items():
                    row[key] = value
            else:
                logger.warning(f"Unexpected feature format for sample {sample.id}")
                continue
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    @staticmethod
    def dataframe_to_arrays(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract feature matrix (X) and labels (y) from DataFrame
        
        Args:
            df: DataFrame with feature columns
            
        Returns:
            (X, y) tuple
        """
        # Get feature columns (all columns starting with 'feature_' or numeric columns)
        feature_cols = [col for col in df.columns if col.startswith('feature_')]
        
        if not feature_cols:
            # Fallback: use all numeric columns except metadata
            exclude_cols = {'sample_id', 'sample_index', 'current_label', 'original_label'}
            feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        X = df[feature_cols].values
        y = df['current_label'].values
        
        return X, y
    
    @staticmethod
    def validate_dataset_format(dataset_id: int, db: Session) -> Dict[str, Any]:
        """
        Validate that dataset is properly formatted for ML pipeline
        
        Returns validation report with any issues found
        """
        samples = db.query(Sample).filter(Sample.dataset_id == dataset_id).limit(10).all()
        
        if not samples:
            return {
                "valid": False,
                "error": "No samples found in dataset"
            }
        
        issues = []
        
        # Check feature format consistency
        first_sample_features = json.loads(samples[0].features)
        expected_length = len(first_sample_features) if isinstance(first_sample_features, list) else None
        
        for sample in samples:
            try:
                features = json.loads(sample.features)
                
                # Check feature length consistency
                if expected_length and len(features) != expected_length:
                    issues.append(f"Sample {sample.id} has inconsistent feature length")
                
                # Check for NaN/None values
                if isinstance(features, list):
                    if any(x is None or (isinstance(x, float) and np.isnan(x)) for x in features):
                        issues.append(f"Sample {sample.id} contains null values")
                
            except Exception as e:
                issues.append(f"Sample {sample.id} has invalid feature format: {e}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "num_samples_checked": len(samples),
            "feature_dimensions": expected_length
        }
    
    @staticmethod
    def get_dataset_info(dataset_id: int, db: Session) -> Dict[str, Any]:
        """
        Get detailed information about dataset structure
        Useful for debugging ML integration issues
        """
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if not dataset:
            return {"error": "Dataset not found"}
        
        # Get sample statistics
        sample = db.query(Sample).filter(Sample.dataset_id == dataset_id).first()
        
        if sample:
            features = json.loads(sample.features)
            feature_example = features[:5] if isinstance(features, list) else str(features)[:100]
        else:
            feature_example = "No samples available"
        
        return {
            "dataset_id": dataset.id,
            "name": dataset.name,
            "num_samples": dataset.num_samples,
            "num_features": dataset.num_features,
            "num_classes": dataset.num_classes,
            "feature_example": feature_example,
            "created_at": dataset.created_at.isoformat() if dataset.created_at else None
        }
    
    @staticmethod
    def prepare_for_ml(
        dataset_id: int,
        db: Session,
        max_samples: int = None
    ) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """
        One-stop function to prepare data for ML pipeline
        
        Returns:
            (X, y, sample_ids) - ready for Dev 1's ML functions
        """
        # Get samples
        query = db.query(Sample).filter(Sample.dataset_id == dataset_id)
        
        if max_samples:
            query = query.limit(max_samples)
        
        samples = query.all()
        
        if not samples:
            raise ValueError(f"No samples found for dataset {dataset_id}")
        
        # Convert to DataFrame
        df = DataPreprocessor.samples_to_dataframe(samples)
        
        # Extract arrays
        X, y = DataPreprocessor.dataframe_to_arrays(df)
        
        # Keep track of sample IDs for mapping results back
        sample_ids = df['sample_id'].tolist()
        
        logger.info(f"Prepared {len(samples)} samples: X shape {X.shape}, y shape {y.shape}")
        
        return X, y, sample_ids