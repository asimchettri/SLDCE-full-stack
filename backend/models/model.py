from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from core.database import Base


class MLModel(Base):
    """ML Model metadata table"""
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False, index=True)
    
    # Model info
    name = Column(String(255), nullable=False)
    model_type = Column(String(100), nullable=False)  # 'RandomForest', 'LogisticRegression', etc.
    description = Column(Text, nullable=True)
    
    # Hyperparameters (stored as JSON)
    hyperparameters = Column(JSON, nullable=True)
    
    # Performance metrics
    train_accuracy = Column(Float, nullable=True)
    test_accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Training info
    num_samples_trained = Column(Integer, nullable=True)
    training_time_seconds = Column(Float, nullable=True)
    
    # Model file path
    model_path = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_baseline = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ModelIteration(Base):
    """Model training iterations/experiments"""
    __tablename__ = "model_iterations"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, nullable=False, index=True)
    dataset_id = Column(Integer, nullable=False, index=True)
    
    # Iteration info
    iteration_number = Column(Integer, nullable=False)
    
    # Performance at this iteration
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Detection metrics
    samples_corrected = Column(Integer, default=0)
    noise_reduced = Column(Float, default=0.0)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())