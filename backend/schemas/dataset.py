from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class DatasetCreate(BaseModel):
    """Schema for creating a new dataset"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    label_column: Optional[str] = Field( 
        default=None,
        description="Name of the label column. Use 'auto' for auto-detection, 'last' for last column, or specify column name"
    )


class DatasetResponse(BaseModel):
    """Schema for dataset response"""
    id: int
    name: str
    description: Optional[str]
    num_samples: int
    num_features: int
    num_classes: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class SampleResponse(BaseModel):
    """Schema for sample response"""
    id: int
    dataset_id: int
    sample_index: int
    current_label: int
    original_label: int
    is_suspicious: bool
    is_corrected: bool
    
    class Config:
        from_attributes = True


class DatasetStats(BaseModel):
    """Dataset statistics"""
    dataset_id: int
    total_samples: int
    num_features: int
    num_classes: int
    class_distribution: Optional[dict] = None
    
    class Config:
        from_attributes = True