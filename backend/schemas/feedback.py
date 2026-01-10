"""
Feedback schemas for API request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List


class FeedbackBase(BaseModel):
    """Base feedback schema"""
    suggestion_id: int
    sample_id: int
    action: str = Field(..., pattern="^(accept|reject|modify)$")
    final_label: int
    iteration: int
    
    model_config = ConfigDict(protected_namespaces=())


class FeedbackCreate(FeedbackBase):
    """Schema for creating feedback"""
    review_time_seconds: Optional[float] = None
    
    model_config = ConfigDict(protected_namespaces=())


class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    id: int
    suggestion_id: int
    sample_id: int
    action: str
    final_label: int
    iteration: int
    review_time_seconds: Optional[float] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class FeedbackWithDetails(FeedbackResponse):
    """Feedback with additional context"""
    current_label: Optional[int] = None
    suggested_label: Optional[int] = None
    original_label: Optional[int] = None
    confidence_score: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class FeedbackStatsResponse(BaseModel):
    """Statistics about feedback for a dataset"""
    dataset_id: int
    total_feedback: int
    accept_count: int
    reject_count: int
    modify_count: int
    acceptance_rate: float
    avg_review_time: Optional[float] = None
    
    model_config = ConfigDict(protected_namespaces=())


class FeedbackPatternResponse(BaseModel):
    """Pattern analysis from feedback"""
    dataset_id: int
    iteration: int
    most_accepted_class: Optional[int] = None
    most_rejected_class: Optional[int] = None
    high_confidence_acceptance_rate: float
    low_confidence_acceptance_rate: float
    
    model_config = ConfigDict(protected_namespaces=())


class FeedbackListResponse(BaseModel):
    """Response for listing feedback"""
    feedback: List[FeedbackResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    model_config = ConfigDict(protected_namespaces=())