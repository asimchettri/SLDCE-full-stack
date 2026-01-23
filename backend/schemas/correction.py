"""
Correction schemas for API request/response validation

"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict


class CorrectionApplyResponse(BaseModel):
    """Response from applying corrections"""
    dataset_id: int
    iteration: int
    total_feedback_processed: int
    corrections_applied: int
    labels_changed: int
    samples_rejected: int
    timestamp: str
    
    model_config = ConfigDict(protected_namespaces=())


class CorrectionSummaryResponse(BaseModel):
    """Summary of corrections for a dataset"""
    dataset_id: int
    total_samples: int
    corrected_samples: int
    labels_changed: int
    suspicious_samples: int
    correction_rate: float
    noise_reduction: float
    original_label_distribution: Dict[int, int]
    current_label_distribution: Dict[int, int]
    
    model_config = ConfigDict(protected_namespaces=())


class CorrectionPreviewResponse(BaseModel):
    """Preview of corrections before applying"""
    dataset_id: int
    iteration: int
    total_changes: int  
    total_feedback: int
    corrections_to_apply: int
    labels_to_change: int
    samples_to_reject: int
    estimated_noise_reduction: float
    changes: list=[]
    
    model_config = ConfigDict(protected_namespaces=())


class CorrectionExportResponse(BaseModel):
    """Response from exporting cleaned dataset"""
    dataset_id: int
    dataset_name: str
    file_path: str
    total_samples: int
    corrected_samples: int
    labels_changed: int
    noise_reduction_percentage: float
    timestamp: str
    
    model_config = ConfigDict(protected_namespaces=())