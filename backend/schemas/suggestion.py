"""
Suggestion schemas for API request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from schemas.detection import DetectionResponse


class SuggestionBase(BaseModel):
    """Base suggestion schema"""
    detection_id: int
    suggested_label: int
    reason: str
    confidence: float = Field(ge=0, le=1)
    
    model_config = ConfigDict(protected_namespaces=())


class SuggestionCreate(SuggestionBase):
    """Schema for creating a suggestion"""
    pass


class SuggestionResponse(BaseModel):
    """Schema for suggestion response"""
    id: int
    detection_id: int
    suggested_label: int
    reason: str
    confidence: float
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class SuggestionWithDetection(SuggestionResponse):
    """Suggestion with full detection details"""
    detection_info: Optional[DetectionResponse] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class SuggestionGenerateRequest(BaseModel):
    """Request to generate suggestions"""
    dataset_id: int
    iteration: int = 1
    top_n: Optional[int] = Field(None, description="Limit to top N suggestions by priority")
    
    model_config = ConfigDict(protected_namespaces=())


class SuggestionGenerateResponse(BaseModel):
    """Response from generating suggestions"""
    dataset_id: int
    iteration: int
    suggestions_created: int
    total_detections: int
    message: Optional[str] = None
    
    model_config = ConfigDict(protected_namespaces=())


class SuggestionListResponse(BaseModel):
    """Response for listing suggestions"""
    suggestions: List[SuggestionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    model_config = ConfigDict(protected_namespaces=())


class SuggestionUpdateRequest(BaseModel):
    """Request to update suggestion status"""
    status: str = Field(..., pattern="^(accepted|rejected|modified)$")
    reviewer_notes: Optional[str] = None
    custom_label: Optional[int] = None  
    
    model_config = ConfigDict(protected_namespaces=())


class SuggestionStatsResponse(BaseModel):
    """Statistics about suggestions"""
    dataset_id: int
    total_suggestions: int
    pending: int
    accepted: int
    rejected: int
    modified: int
    acceptance_rate: float
    
    model_config = ConfigDict(protected_namespaces=())