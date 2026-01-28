"""
Correction service - Apply human feedback corrections to dataset
CRITICAL: Updates sample labels based on accepted feedback
"""
from sqlalchemy.orm import Session
from models.dataset import Sample, Feedback, Suggestion
from fastapi import HTTPException
from typing import Dict, Any, List
import json
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CorrectionService:
    """Service for applying corrections from human feedback"""
    
    @staticmethod
    def apply_corrections(
        db: Session,
        dataset_id: int,
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Apply all accepted feedback corrections to the dataset
        
        Workflow:
        1. Get all feedback for this dataset/iteration
        2. Update sample labels based on accepted/modified feedback
        3. Mark samples as corrected
        4. Track correction statistics
        
        Args:
            db: Database session
            dataset_id: Dataset to apply corrections to
            iteration: Iteration number (default: 1 for Phase 1)
            
        Returns:
            Statistics about corrections applied
        """
        logger.info(f"🔧 Applying corrections to dataset {dataset_id}, iteration {iteration}")
        
        # Get all feedback for this dataset
        feedback_list = db.query(Feedback).join(
            Sample, Feedback.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id,
            Feedback.iteration == iteration
        ).all()
        
        if not feedback_list:
            raise HTTPException(
                status_code=404,
                detail=f"No feedback found for dataset {dataset_id}, iteration {iteration}"
            )
        
        # Track corrections
        corrections_applied = 0
        labels_changed = 0
        samples_rejected = 0
        
        for feedback in feedback_list:
            sample = db.query(Sample).filter(Sample.id == feedback.sample_id).first()
            
            if not sample:
                logger.warning(f"Sample {feedback.sample_id} not found, skipping")
                continue
            
            # Store old label for comparison
            old_label = sample.current_label
            
            # Apply correction based on action
            if feedback.action == 'accept':
                # Accept suggestion - update to suggested label
                sample.current_label = feedback.final_label
                sample.is_corrected = True
                corrections_applied += 1
                
                if old_label != feedback.final_label:
                    labels_changed += 1
                    logger.info(f"✅ Sample {sample.id}: {old_label} → {feedback.final_label} (accepted)")
            
            elif feedback.action == 'modify':
                # Human modified the suggestion - use their custom label
                sample.current_label = feedback.final_label
                sample.is_corrected = True
                corrections_applied += 1
                
                if old_label != feedback.final_label:
                    labels_changed += 1
                    logger.info(f"✏️  Sample {sample.id}: {old_label} → {feedback.final_label} (modified)")
            
            elif feedback.action == 'reject':
                # Rejected - keep original label, but mark as reviewed
                sample.is_corrected = False  # Not actually corrected
                samples_rejected += 1
                logger.info(f"❌ Sample {sample.id}: Kept label {old_label} (rejected)")
        
        # Commit all changes
        db.commit()
        
        logger.info(f"✅ Applied {corrections_applied} corrections, {labels_changed} labels changed")
        
        return {
            "dataset_id": dataset_id,
            "iteration": iteration,
            "total_feedback_processed": len(feedback_list),
            "corrections_applied": corrections_applied,
            "labels_changed": labels_changed,
            "samples_rejected": samples_rejected,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def export_cleaned_dataset(
        db: Session,
        dataset_id: int,
        output_dir: str = "cleaned_datasets"
    ) -> Dict[str, Any]:
        """
        Export cleaned dataset to CSV file
        UPDATED: Preserves original column names from upload
        """
        from models.dataset import Dataset
        
        logger.info(f"📤 Exporting cleaned dataset {dataset_id}")
        
        # Get dataset metadata
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get all samples ordered by original index
        samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id
        ).order_by(Sample.sample_index).all()
        
        if not samples:
            raise HTTPException(status_code=404, detail="No samples found in dataset")
    
    # Get original column names
        try:
            feature_names = json.loads(dataset.feature_names) if dataset.feature_names else None
            label_column_name = dataset.label_column_name or 'label'
        except (json.JSONDecodeError, TypeError):
            logger.warning("Could not parse feature names, using generic names")
            feature_names = None
            label_column_name = 'label'
        
        # Convert to DataFrame
        records = []
        for sample in samples:
            # Parse features
            features = json.loads(sample.features)
            
            # Create record with features + label
            record = {}
            
            # Add features with original names if available
            if isinstance(features, list):
                if feature_names and len(feature_names) == len(features):
                    # Use original column names
                    for col_name, feature_value in zip(feature_names, features):
                        record[col_name] = feature_value
                else:
                    # Fallback to generic names
                    for i, feature_value in enumerate(features):
                        record[f'feature_{i}'] = feature_value
            elif isinstance(features, dict):
                record.update(features)
            
            # Add label with original column name
            record[label_column_name] = sample.current_label
            
            records.append(record)
    
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Reorder columns: features first, then label (matching original order)
        if feature_names:
            columns_order = feature_names + [label_column_name]
            df = df[columns_order]
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{dataset.name.replace(' ', '_')}_cleaned_{timestamp}.csv"
        file_path = os.path.join(output_dir, filename)
        
        # Save to CSV
        df.to_csv(file_path, index=False)
        
        # Calculate stats
        corrected_samples = sum(1 for s in samples if s.is_corrected)
        labels_changed = sum(
            1 for s in samples 
            if s.original_label != s.current_label
        )
        
        logger.info(f"✅ Exported cleaned dataset to {file_path}")
        logger.info(f"   - Total samples: {len(samples)}")
        logger.info(f"   - Corrected samples: {corrected_samples}")
        logger.info(f"   - Labels changed: {labels_changed}")
        logger.info(f"   - Column names preserved: {feature_names is not None}")
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "file_path": file_path,
            "total_samples": len(samples),
            "corrected_samples": corrected_samples,
            "labels_changed": labels_changed,
            "noise_reduction_percentage": round(
                (labels_changed / len(samples) * 100) if len(samples) > 0 else 0,
                2
            ),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_correction_summary(
        db: Session,
        dataset_id: int
    ) -> Dict[str, Any]:
        """
        Get summary of corrections applied to a dataset
        
        Shows before/after comparison of labels
        """
        samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id
        ).all()
        
        if not samples:
            raise HTTPException(status_code=404, detail="No samples found")
        
        total = len(samples)
        corrected = sum(1 for s in samples if s.is_corrected)
        labels_changed = sum(1 for s in samples if s.original_label != s.current_label)
        suspicious = sum(1 for s in samples if s.is_suspicious)
        
        # Calculate label distribution
        from collections import Counter
        original_distribution = Counter(s.original_label for s in samples)
        current_distribution = Counter(s.current_label for s in samples)
        
        return {
            "dataset_id": dataset_id,
            "total_samples": total,
            "corrected_samples": corrected,
            "labels_changed": labels_changed,
            "suspicious_samples": suspicious,
            "correction_rate": round((corrected / total * 100) if total > 0 else 0, 2),
            "noise_reduction": round((labels_changed / total * 100) if total > 0 else 0, 2),
            "original_label_distribution": dict(original_distribution),
            "current_label_distribution": dict(current_distribution)
        }