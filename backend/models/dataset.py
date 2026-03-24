from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)

    num_samples = Column(Integer, nullable=False)
    num_features = Column(Integer, nullable=False)
    num_classes = Column(Integer, nullable=False)

    feature_names = Column(Text, nullable=True)
    label_column_name = Column(String(255), nullable=True)
    label_mapping = Column(Text, nullable=True)  # FIX 24: dedicated JSON column

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    is_active = Column(Boolean, default=True)


class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)

    sample_index = Column(Integer, nullable=False)
    features = Column(Text, nullable=False)
    original_label = Column(Integer, nullable=False)
    current_label = Column(Integer, nullable=False)

    is_suspicious = Column(Boolean, default=False)
    is_corrected = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id", ondelete="CASCADE"), nullable=False, index=True)
    iteration = Column(Integer, nullable=False)

    confidence_score = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    predicted_label = Column(Integer, nullable=False)

    entropy_score = Column(Float, nullable=True)
    distance_score = Column(Float, nullable=True)
    signal_breakdown = Column(Text, nullable=True)

    priority_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=True)
    priority_weights = Column(Text, nullable=True)

    detected_at = Column(DateTime(timezone=True), server_default=func.now())


class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id", ondelete="CASCADE"), nullable=False, index=True)

    suggested_label = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)

    status = Column(String(50), nullable=False, default="pending", index=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewer_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    suggestion_id = Column(Integer, ForeignKey("suggestions.id", ondelete="CASCADE"), nullable=False, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id", ondelete="CASCADE"), nullable=False, index=True)

    # Valid actions: 'approve', 'reject', 'modify', 'uncertain'
    action = Column(String(50), nullable=False)
    final_label = Column(Integer, nullable=False)

    iteration = Column(Integer, nullable=False)
    review_time_seconds = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)

    tool = Column(String(50), nullable=False)
    iteration = Column(Integer, nullable=False, default=1)

    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    f1 = Column(Float, nullable=True)

    human_effort = Column(Integer, nullable=True)
    meta = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())