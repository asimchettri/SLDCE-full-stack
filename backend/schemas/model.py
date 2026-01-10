from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any


class MLModelCreate(BaseModel):
    """Schema for creating a new ML model"""
    dataset_id: int
    name: str = Field(..., min_length=1, max_length=255)
    model_type: str
    description: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(protected_namespaces=())


class MLModelResponse(BaseModel):
    """Schema for ML model response"""
    id: int
    dataset_id: int
    name: str
    model_type: str
    description: Optional[str]
    hyperparameters: Optional[Dict[str, Any]]
    train_accuracy: Optional[float]
    test_accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    num_samples_trained: Optional[int]
    training_time_seconds: Optional[float]
    is_active: bool
    is_baseline: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ModelIterationResponse(BaseModel):
    """Schema for model iteration response"""
    id: int
    model_id: int
    dataset_id: int
    iteration_number: int
    accuracy: float
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    samples_corrected: int
    noise_reduced: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ModelComparisonResponse(BaseModel):
    """Schema for comparing multiple models"""
    model_id: int
    name: str
    model_type: str
    accuracy: float
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    training_time: Optional[float]
    is_baseline: bool
    
    model_config = ConfigDict(protected_namespaces=())