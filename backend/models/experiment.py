from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from core.database import Base


class Experiment(Base):
    """Experiment tracking table"""
    __tablename__ = "experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False, index=True)
    
    # Experiment info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default='running')  # 'running', 'completed', 'failed'
    
    # Configuration
    noise_percentage = Column(Float, nullable=False)
    detection_threshold = Column(Float, default=0.7)
    max_iterations = Column(Integer, default=10)
    
    # Current state
    current_iteration = Column(Integer, default=0)
    
    # Overall metrics
    baseline_accuracy = Column(Float, nullable=True)  # Accuracy on noisy data
    final_accuracy = Column(Float, nullable=True)     # Accuracy after corrections
    total_corrections = Column(Integer, default=0)
    total_time_seconds = Column(Float, nullable=True)
    
    # Results summary (JSON)
    iteration_results = Column(JSON, nullable=True)  # Store all iteration metrics
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class ExperimentIteration(Base):
    """Individual iteration results within an experiment"""
    __tablename__ = "experiment_iterations"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, nullable=False, index=True)
    iteration_number = Column(Integer, nullable=False)
    
    # Model performance
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Detection metrics
    samples_flagged = Column(Integer, default=0)
    samples_corrected = Column(Integer, default=0)
    correction_acceptance_rate = Column(Float, nullable=True)
    
    # Data quality
    remaining_noise_percentage = Column(Float, nullable=True)
    samples_reviewed = Column(Integer, default=0)
    
    # Performance
    iteration_time_seconds = Column(Float, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())