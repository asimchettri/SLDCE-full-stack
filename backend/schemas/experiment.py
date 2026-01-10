from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


class ExperimentCreate(BaseModel):
    """Schema for creating a new experiment"""
    dataset_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    noise_percentage: float = Field(..., ge=0, le=100)
    detection_threshold: float = Field(default=0.7, ge=0, le=1)
    max_iterations: int = Field(default=10, ge=1, le=50)
    
    model_config = ConfigDict(protected_namespaces=())


class ExperimentResponse(BaseModel):
    """Schema for experiment response"""
    id: int
    dataset_id: int
    name: str
    description: Optional[str]
    status: str
    noise_percentage: float
    detection_threshold: float
    max_iterations: int
    current_iteration: int
    baseline_accuracy: Optional[float]
    final_accuracy: Optional[float]
    total_corrections: int
    total_time_seconds: Optional[float]
    iteration_results: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ExperimentIterationResponse(BaseModel):
    """Schema for experiment iteration response"""
    id: int
    experiment_id: int
    iteration_number: int
    accuracy: float
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    samples_flagged: int
    samples_corrected: int
    correction_acceptance_rate: Optional[float]
    remaining_noise_percentage: Optional[float]
    samples_reviewed: int
    iteration_time_seconds: Optional[float]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ExperimentSummary(BaseModel):
    """Summary statistics for an experiment"""
    experiment_id: int
    name: str
    status: str
    total_iterations: int
    accuracy_improvement: float
    noise_reduction: float
    total_corrections: int
    avg_time_per_iteration: float
    
    model_config = ConfigDict(protected_namespaces=())