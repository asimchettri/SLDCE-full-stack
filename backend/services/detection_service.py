"""
Detection service - Business logic for error detection
"""
from sqlalchemy.orm import Session
from models.dataset import Sample, Detection, Suggestion
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
import json
import random
from datetime import datetime


class DetectionService:
    """Service class for detection operations"""
    
    @staticmethod
    def calculate_priority_score(
        confidence: float,
        anomaly: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Calculate priority score with configurable weights
        Default: 60% confidence, 40% anomaly
        """
        if weights is None:
            weights = {"confidence": 0.6, "anomaly": 0.4}
        
        priority = (
            confidence * weights.get("confidence", 0.6) +
            anomaly * weights.get("anomaly", 0.4)
        )
        return min(max(priority, 0.0), 1.0)  # Clamp between 0 and 1
    
    @staticmethod
    def run_detection(
        db: Session,
        dataset_id: int,
        confidence_threshold: float = 0.7,
        max_samples: int = None,
        priority_weights: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Run detection on a dataset to identify suspicious samples
        
        This is a simplified version for Phase 1.
        In Phase 2, this will integrate with Dev 1's ML detection algorithms.
        """
        
        # Get all samples from dataset
        samples_query = db.query(Sample).filter(Sample.dataset_id == dataset_id)
        
        if max_samples:
            samples_query = samples_query.limit(max_samples)
        
        samples = samples_query.all()
        
        if not samples:
            raise HTTPException(
                status_code=404,
                detail=f"No samples found for dataset {dataset_id}"
            )
        
        # Simulate detection (Phase 1 - Placeholder)
        detections_created = 0
        iteration = 1
        
        for sample in samples:
            is_mislabeled = sample.original_label != sample.current_label
            
            if is_mislabeled:
                confidence_score = random.uniform(0.75, 0.95)
                anomaly_score = random.uniform(0.65, 0.90)
                
                # Use configurable priority calculation
                priority_score = DetectionService.calculate_priority_score(
                    confidence_score, 
                    anomaly_score, 
                    priority_weights
                )
                
                # Store signal breakdown
                signal_breakdown = {
                    "confidence": confidence_score,
                    "anomaly": anomaly_score,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                detection = Detection(
                    sample_id=sample.id,
                    iteration=iteration,
                    confidence_score=confidence_score,
                    anomaly_score=anomaly_score,
                    predicted_label=sample.original_label,
                    priority_score=priority_score,
                    signal_breakdown=json.dumps(signal_breakdown),
                    priority_weights=json.dumps(priority_weights) if priority_weights else None
                )
                
                db.add(detection)
                sample.is_suspicious = True
                detections_created += 1
        
        db.commit()
        
        total_samples = len(samples)
        suspicious_count = detections_created
        detection_rate = (suspicious_count / total_samples * 100) if total_samples > 0 else 0
        
        return {
            "dataset_id": dataset_id,
            "iteration": iteration,
            "total_samples_analyzed": total_samples,
            "suspicious_samples_found": suspicious_count,
            "detection_rate": round(detection_rate, 2),
            "confidence_threshold": confidence_threshold,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_detections(
        db: Session,
        dataset_id: int = None,
        iteration: int = None,
        min_priority: float = None,
        min_confidence: float = None,
        min_anomaly: float = None,
        signal_type: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Detection]:
        """Get detections with optional filters including signal-specific filters"""
        query = db.query(Detection)
        
        if dataset_id:
            query = query.join(Sample, Detection.sample_id == Sample.id).filter(Sample.dataset_id == dataset_id)
        
        if iteration:
            query = query.filter(Detection.iteration == iteration)
        
        if min_priority:
            query = query.filter(Detection.priority_score >= min_priority)
        
        # Signal-specific filters
        if min_confidence:
            query = query.filter(Detection.confidence_score >= min_confidence)
        
        if min_anomaly:
            query = query.filter(Detection.anomaly_score >= min_anomaly)
        
        # Filter by dominant signal
        if signal_type == "confidence":
            query = query.filter(Detection.confidence_score > Detection.anomaly_score)
        elif signal_type == "anomaly":
            query = query.filter(Detection.anomaly_score > Detection.confidence_score)
        elif signal_type == "both":
            query = query.filter(Detection.confidence_score >= 0.7, Detection.anomaly_score >= 0.7)
        
        query = query.order_by(Detection.priority_score.desc())
        
        return query.offset(offset).limit(limit).all()
    
    @staticmethod
    def get_detection_by_id(db: Session, detection_id: int) -> Detection:
        """Get specific detection by ID"""
        detection = db.query(Detection).filter(Detection.id == detection_id).first()
        
        if not detection:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        return detection
    
    @staticmethod
    def get_detection_with_sample(db: Session, detection_id: int) -> Dict[str, Any]:
        """Get detection with associated sample details"""
        detection = DetectionService.get_detection_by_id(db, detection_id)
        sample = db.query(Sample).filter(Sample.id == detection.sample_id).first()
        
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        
        # Parse signal breakdown if available
        signal_breakdown = None
        if detection.signal_breakdown:
            try:
                signal_breakdown = json.loads(detection.signal_breakdown)
            except:
                signal_breakdown = None
        
        # Parse priority weights if available
        priority_weights = None
        if detection.priority_weights:
            try:
                priority_weights = json.loads(detection.priority_weights)
            except:
                priority_weights = None
        
        return {
            "detection_id": detection.id,
            "sample_id": sample.id,
            "features": json.loads(sample.features),
            "current_label": sample.current_label,
            "predicted_label": detection.predicted_label,
            "original_label": sample.original_label,
            "confidence_score": detection.confidence_score,
            "anomaly_score": detection.anomaly_score,
            "priority_score": detection.priority_score,
            "iteration": detection.iteration,
            "detected_at": detection.detected_at.isoformat() if detection.detected_at else None,
            "signal_breakdown": signal_breakdown,
            "priority_weights": priority_weights
        }
    
    @staticmethod
    def generate_suggestions(
        db: Session,
        dataset_id: int,
        iteration: int = 1
    ) -> Dict[str, Any]:
        """Generate correction suggestions for detected samples"""
        
        detections = db.query(Detection).join(Sample, Detection.sample_id == Sample.id).filter(
            Sample.dataset_id == dataset_id,
            Detection.iteration == iteration
        ).order_by(Detection.priority_score.desc()).all()
        
        if not detections:
            return {
                "dataset_id": dataset_id,
                "iteration": iteration,
                "suggestions_created": 0,
                "message": "No detections found for this iteration"
            }
        
        suggestions_created = 0
        
        for detection in detections:
            existing = db.query(Suggestion).filter(
                Suggestion.detection_id == detection.id
            ).first()
            
            if existing:
                continue
            
            reason = f"High confidence ({detection.confidence_score:.2%}) disagreement with current label. "
            reason += f"Anomaly score: {detection.anomaly_score:.2%}. "
            reason += "Model predicts different class based on feature patterns."
            
            suggestion = Suggestion(
                detection_id=detection.id,
                suggested_label=detection.predicted_label,
                reason=reason,
                confidence=detection.confidence_score
            )
            
            db.add(suggestion)
            suggestions_created += 1
        
        db.commit()
        
        return {
            "dataset_id": dataset_id,
            "iteration": iteration,
            "suggestions_created": suggestions_created,
            "total_detections": len(detections)
        }
    
    @staticmethod
    def get_detection_stats(db: Session, dataset_id: int) -> Dict[str, Any]:
        """Get detection statistics for a dataset"""
        
        total_samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id
        ).count()
        
        suspicious_samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id,
            Sample.is_suspicious == True
        ).count()
        
        total_detections = db.query(Detection).select_from(Detection).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id
        ).count()
        
        high_priority = db.query(Detection).select_from(Detection).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id,
            Detection.priority_score >= 0.8
        ).count()
        
        from sqlalchemy import func
        
        avg_confidence_result = db.query(
            func.avg(Detection.confidence_score)
        ).select_from(Detection).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id
        ).scalar()
        
        avg_confidence = float(avg_confidence_result) if avg_confidence_result else 0
        
        return {
            "dataset_id": dataset_id,
            "total_samples": total_samples,
            "suspicious_samples": suspicious_samples,
            "total_detections": total_detections,
            "high_priority_detections": high_priority,
            "average_confidence": round(avg_confidence, 4),
            "detection_rate": round(
                (suspicious_samples / total_samples * 100)
                if total_samples > 0 else 0,
                2
            )
        }
    
    @staticmethod
    def get_signal_stats(db: Session, dataset_id: int) -> Dict[str, Any]:
        """Get signal-specific statistics"""
        from sqlalchemy import func
        
        detections = db.query(Detection).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id
        ).all()
        
        if not detections:
            return {
                "dataset_id": dataset_id,
                "total_detections": 0,
                "confidence_dominant": 0,
                "anomaly_dominant": 0,
                "both_high": 0,
                "avg_confidence": 0,
                "avg_anomaly": 0
            }
        
        confidence_dominant = sum(1 for d in detections if d.confidence_score > d.anomaly_score)
        anomaly_dominant = sum(1 for d in detections if d.anomaly_score > d.confidence_score)
        both_high = sum(1 for d in detections if d.confidence_score >= 0.7 and d.anomaly_score >= 0.7)
        
        avg_confidence = sum(d.confidence_score for d in detections) / len(detections)
        avg_anomaly = sum(d.anomaly_score for d in detections) / len(detections)
        
        return {
            "dataset_id": dataset_id,
            "total_detections": len(detections),
            "confidence_dominant": confidence_dominant,
            "anomaly_dominant": anomaly_dominant,
            "both_high": both_high,
            "avg_confidence": round(avg_confidence, 4),
            "avg_anomaly": round(avg_anomaly, 4)
        }