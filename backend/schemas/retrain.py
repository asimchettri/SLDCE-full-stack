"""
Retrain schemas for API request/response validation

"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Any, Optional


class RetrainRequest(BaseModel):
    """Request to retrain model"""
    dataset_id: int
    iteration: int = Field(default=1, ge=1)
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    
    model_config = ConfigDict(protected_namespaces=())


class MetricsResponse(BaseModel):
    """Model metrics"""
    accuracy: float
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    test_accuracy: Optional[float] = None
    
    model_config = ConfigDict(protected_namespaces=())


class ImprovementResponse(BaseModel):
    """Improvement metrics"""
    absolute: float
    percentage: float
    
    model_config = ConfigDict(protected_namespaces=())


class TrainingInfoResponse(BaseModel):
    """Training information"""
    samples_trained: int
    samples_tested: int
    training_time_seconds: float
    samples_corrected: int
    labels_changed: int
    noise_reduced_pct: float
    
    model_config = ConfigDict(protected_namespaces=())


class RetrainResponse(BaseModel):
    """Response from retraining model"""
    dataset_id: int
    iteration: int
    baseline_model_id: Optional[int]
    retrained_model_id: int
    baseline_metrics: MetricsResponse
    retrained_metrics: MetricsResponse
    improvement: ImprovementResponse
    training_info: TrainingInfoResponse
    timestamp: str
    
    model_config = ConfigDict(protected_namespaces=())


class ModelComparisonItem(BaseModel):
    """Single model in comparison"""
    model_id: int
    name: str
    model_type: str
    is_baseline: bool
    accuracy: float
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    training_time: Optional[float]
    samples_trained: Optional[int]
    iteration_number: Optional[int]
    samples_corrected: Optional[int]
    noise_reduced: Optional[float]
    created_at: Optional[str]
    
    model_config = ConfigDict(protected_namespaces=())


class ModelComparisonResponse(BaseModel):
    """Response from comparing models"""
    dataset_id: int
    total_models: int
    models: list[ModelComparisonItem]
    overall_improvement: Optional[ImprovementResponse]
    
    model_config = ConfigDict(protected_namespaces=())