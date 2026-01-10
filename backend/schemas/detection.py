from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


class SignalWeights(BaseModel):
    """Configurable weights for priority calculation"""
    confidence: float = Field(default=0.6, ge=0, le=1)
    anomaly: float = Field(default=0.4, ge=0, le=1)
    
    model_config = ConfigDict(protected_namespaces=())


class SignalBreakdown(BaseModel):
    """Individual signal scores"""
    confidence: float
    anomaly: float
    entropy: Optional[float] = None
    distance: Optional[float] = None
    timestamp: Optional[str] = None
    
    model_config = ConfigDict(protected_namespaces=())


class DetectionRunRequest(BaseModel):
    """Request to run detection on a dataset"""
    dataset_id: int
    confidence_threshold: float = Field(default=0.7, ge=0, le=1)
    max_samples: Optional[int] = None
    priority_weights: Optional[Dict[str, float]] = None
    
    model_config = ConfigDict(protected_namespaces=())


class DetectionRunResponse(BaseModel):
    """Response from running detection"""
    dataset_id: int
    iteration: int
    total_samples_analyzed: int
    suspicious_samples_found: int
    detection_rate: float
    confidence_threshold: float
    timestamp: str
    
    model_config = ConfigDict(protected_namespaces=())


class DetectionResponse(BaseModel):
    """Schema for detection response"""
    id: int
    sample_id: int
    iteration: int
    confidence_score: float
    anomaly_score: float
    predicted_label: int
    priority_score: float
    rank: Optional[int]
    detected_at: datetime
    entropy_score: Optional[float] = None
    distance_score: Optional[float] = None
    signal_breakdown: Optional[str] = None  # JSON string
    priority_weights: Optional[str] = None  # JSON string
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class DetectionWithSampleResponse(BaseModel):
    """Detection with sample details"""
    detection_id: int
    sample_id: int
    features: List[float]
    current_label: int
    predicted_label: int
    original_label: int
    confidence_score: float
    anomaly_score: float
    priority_score: float
    iteration: Optional[int] = None
    detected_at: Optional[str] = None
    signal_breakdown: Optional[Dict[str, Any]] = None
    priority_weights: Optional[Dict[str, float]] = None
    
    model_config = ConfigDict(protected_namespaces=())


class SuggestionGenerateResponse(BaseModel):
    """Response from generating suggestions"""
    dataset_id: int
    iteration: int
    suggestions_created: int
    total_detections: int
    message: Optional[str] = None
    
    model_config = ConfigDict(protected_namespaces=())


class DetectionStatsResponse(BaseModel):
    """Detection statistics"""
    dataset_id: int
    total_samples: int
    suspicious_samples: int
    total_detections: int
    high_priority_detections: int
    average_confidence: float
    detection_rate: float
    
    model_config = ConfigDict(protected_namespaces=())


class SignalStatsResponse(BaseModel):
    """Signal-specific statistics"""
    dataset_id: int
    total_detections: int
    confidence_dominant: int
    anomaly_dominant: int
    both_high: int
    avg_confidence: float
    avg_anomaly: float
    
    model_config = ConfigDict(protected_namespaces=())