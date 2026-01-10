from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from core.database import Base


class Dataset(Base):
    """Dataset metadata table"""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)
    
    # Metadata
    num_samples = Column(Integer, nullable=False)
    num_features = Column(Integer, nullable=False)
    num_classes = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Status
    is_active = Column(Boolean, default=True)


class Sample(Base):
    """Individual data samples table"""
    __tablename__ = "samples"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False, index=True)
    
    # Data
    sample_index = Column(Integer, nullable=False)  # Original index in dataset
    features = Column(Text, nullable=False)  # JSON string of features
    original_label = Column(Integer, nullable=False)
    current_label = Column(Integer, nullable=False)  # Can be corrected
    
    # Flags
    is_suspicious = Column(Boolean, default=False)
    is_corrected = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Detection(Base):
    """Detected suspicious samples table"""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, nullable=False, index=True)
    iteration = Column(Integer, nullable=False)
    
    # Detection metrics
    confidence_score = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    predicted_label = Column(Integer, nullable=False)
    
    # Additional signal scores for future extensibility
    entropy_score = Column(Float, nullable=True)
    distance_score = Column(Float, nullable=True)
    
    # Signal metadata (flexible JSON for future signals)
    signal_breakdown = Column(Text, nullable=True)  # JSON: {"signal_name": score}
    
    # Priority
    priority_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=True)
    
    # Priority calculation config
    priority_weights = Column(Text, nullable=True)  # JSON: {"confidence": 0.6, "anomaly": 0.4}
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())


class Suggestion(Base):
    """Correction suggestions table"""
    __tablename__ = "suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, nullable=False, index=True)
    
    # Suggestion
    suggested_label = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Status tracking (NEW)
    status = Column(String(50), nullable=False, default='pending', index=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Feedback(Base):
    """Human feedback table - CRITICAL for learning"""
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    suggestion_id = Column(Integer, nullable=False, index=True)
    sample_id = Column(Integer, nullable=False, index=True)
    
    # Decision
    action = Column(String(50), nullable=False)  # 'accept', 'reject', 'modify'
    final_label = Column(Integer, nullable=False)
    
    # Context
    iteration = Column(Integer, nullable=False)
    review_time_seconds = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())