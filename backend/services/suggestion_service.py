"""
Suggestion service - Business logic for correction suggestions
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.dataset import Sample, Detection, Suggestion
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import math


class SuggestionService:
    """Service class for suggestion operations"""
    
    @staticmethod
    def generate_suggestions(
        db: Session,
        dataset_id: int,
        iteration: int = 1,
        top_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate correction suggestions for detected samples
        
        Phase 1: Uses detection priority score for ranking
        Phase 2: Will add historical acceptance rate, class frequency
        """
        
        # Get detections ordered by priority (highest first)
        detections_query = db.query(Detection).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id,
            Detection.iteration == iteration
        ).order_by(Detection.priority_score.desc())
        
        # Apply top_n limit if specified
        if top_n:
            detections_query = detections_query.limit(top_n)
        
        detections = detections_query.all()
        
        if not detections:
            return {
                "dataset_id": dataset_id,
                "iteration": iteration,
                "suggestions_created": 0,
                "total_detections": 0,
                "message": "No detections found for this iteration"
            }
        
        suggestions_created = 0
        
        for detection in detections:
            # Check if suggestion already exists
            existing = db.query(Suggestion).filter(
                Suggestion.detection_id == detection.id
            ).first()
            
            if existing:
                continue
            
            # Generate reason based on signals
            reason = f"High confidence ({detection.confidence_score:.2%}) disagreement with current label. "
            reason += f"Anomaly score: {detection.anomaly_score:.2%}. "
            
            # Add signal-specific reasoning
            if detection.confidence_score > 0.85:
                reason += "Model is very confident about alternative label. "
            if detection.anomaly_score > 0.85:
                reason += "Sample shows strong anomalous behavior for current class. "
            if detection.confidence_score >= 0.7 and detection.anomaly_score >= 0.7:
                reason += "Both signals agree - high likelihood of mislabeling."
            
            # Create suggestion
            suggestion = Suggestion(
                detection_id=detection.id,
                suggested_label=detection.predicted_label,
                reason=reason.strip(),
                confidence=detection.confidence_score,
                status='pending'  # New field
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
    def get_suggestions(
        db: Session,
        dataset_id: Optional[int] = None,
        iteration: Optional[int] = None,
        status: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Suggestion]:
        """Get suggestions with optional filters"""
        
        query = db.query(Suggestion)
        
        # Join with Detection and Sample for filtering
        if dataset_id or iteration:
            query = query.join(Detection, Suggestion.detection_id == Detection.id)
            query = query.join(Sample, Detection.sample_id == Sample.id)
        
        # Apply filters
        if dataset_id:
            query = query.filter(Sample.dataset_id == dataset_id)
        
        if iteration:
            query = query.filter(Detection.iteration == iteration)
        
        if status:
            query = query.filter(Suggestion.status == status)
        
        if min_confidence:
            query = query.filter(Suggestion.confidence >= min_confidence)
        
        # Order by confidence (highest first)
        query = query.order_by(Suggestion.confidence.desc())
        
        return query.offset(offset).limit(limit).all()
    
    @staticmethod
    def get_suggestion_by_id(db: Session, suggestion_id: int) -> Suggestion:
        """Get specific suggestion by ID"""
        suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
        
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        return suggestion
    
    @staticmethod
    def get_suggestion_with_detection(
        db: Session,
        suggestion_id: int
    ) -> Dict[str, Any]:
        """Get suggestion with full detection details"""
        suggestion = SuggestionService.get_suggestion_by_id(db, suggestion_id)
        
        # Get associated detection
        detection = db.query(Detection).filter(
            Detection.id == suggestion.detection_id
        ).first()
        
        if not detection:
            raise HTTPException(status_code=404, detail="Associated detection not found")
        
        # Get associated sample
        sample = db.query(Sample).filter(Sample.id == detection.sample_id).first()
        
        if not sample:
            raise HTTPException(status_code=404, detail="Associated sample not found")
        
        import json
        
        return {
            "suggestion_id": suggestion.id,
            "detection_id": detection.id,
            "sample_id": sample.id,
            "suggested_label": suggestion.suggested_label,
            "current_label": sample.current_label,
            "predicted_label": detection.predicted_label,
            "original_label": sample.original_label,
            "reason": suggestion.reason,
            "confidence": suggestion.confidence,
            "status": suggestion.status,
            "created_at": suggestion.created_at.isoformat() if suggestion.created_at else None,
            "reviewed_at": suggestion.reviewed_at.isoformat() if suggestion.reviewed_at else None,
            "reviewer_notes": suggestion.reviewer_notes,
            "detection_info": {
                "confidence_score": detection.confidence_score,
                "anomaly_score": detection.anomaly_score,
                "priority_score": detection.priority_score,
                "iteration": detection.iteration
            },
            "sample_features": json.loads(sample.features)
        }
    
    @staticmethod
    def update_suggestion_status(
        db: Session,
        suggestion_id: int,
        status: str,
        reviewer_notes: Optional[str] = None,
        custom_label: Optional[int] = None  
    ) -> Suggestion:
        """
        
        IMPORTANT: Also creates Feedback record for Phase 2 learning system
        """
        from services.feedback_service import FeedbackService
        
        suggestion = SuggestionService.get_suggestion_by_id(db, suggestion_id)
        
        # Validate status
        valid_statuses = ['accepted', 'rejected', 'modified']
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Get detection and sample to determine final label
        detection = db.query(Detection).filter(
            Detection.id == suggestion.detection_id
        ).first()
        
        sample = db.query(Sample).filter(Sample.id == detection.sample_id).first()
        
        # Determine final label based on action
        if status == 'accepted':
            final_label = suggestion.suggested_label
            action = 'accept'
        elif status == 'rejected':
            final_label = sample.current_label
            action = 'reject'
        else:
            # Use custom label from user input
            if custom_label is None:
                raise HTTPException(
                    status_code=400,
                    detail="custom_label is required when status is 'modified'"
                )
            final_label = custom_label
            action = 'modify'
        
        # Update suggestion
        suggestion.status = status
        suggestion.reviewed_at = datetime.utcnow()
        
        if reviewer_notes:
            suggestion.reviewer_notes = reviewer_notes
        
        db.commit()
        db.refresh(suggestion)
        
        # CRITICAL: Create feedback record for learning system
        FeedbackService.create_feedback_from_suggestion(
            db,
            suggestion=suggestion,
            action=action,
            final_label=final_label
        )
        
        return suggestion
    


    
    @staticmethod
    def get_suggestion_stats(db: Session, dataset_id: int) -> Dict[str, Any]:
        """Get statistics about suggestions for a dataset"""
        
        # Get all suggestions for this dataset
        suggestions = db.query(Suggestion).join(
            Detection, Suggestion.detection_id == Detection.id
        ).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id
        ).all()
        
        total = len(suggestions)
        
        if total == 0:
            return {
                "dataset_id": dataset_id,
                "total_suggestions": 0,
                "pending": 0,
                "accepted": 0,
                "rejected": 0,
                "modified": 0,
                "acceptance_rate": 0.0
            }
        
        # Count by status
        pending = sum(1 for s in suggestions if s.status == 'pending')
        accepted = sum(1 for s in suggestions if s.status == 'accepted')
        rejected = sum(1 for s in suggestions if s.status == 'rejected')
        modified = sum(1 for s in suggestions if s.status == 'modified')
        
        # Calculate acceptance rate (accepted + modified = positive outcomes)
        reviewed = total - pending
        acceptance_rate = ((accepted + modified) / reviewed * 100) if reviewed > 0 else 0.0
        
        return {
            "dataset_id": dataset_id,
            "total_suggestions": total,
            "pending": pending,
            "accepted": accepted,
            "rejected": rejected,
            "modified": modified,
            "acceptance_rate": round(acceptance_rate, 2)
        }
    
    @staticmethod
    def count_suggestions(
        db: Session,
        dataset_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> int:
        """Count suggestions with filters"""
        query = db.query(func.count(Suggestion.id))
        
        if dataset_id or status:
            query = query.join(Detection, Suggestion.detection_id == Detection.id)
            query = query.join(Sample, Detection.sample_id == Sample.id)
        
        if dataset_id:
            query = query.filter(Sample.dataset_id == dataset_id)
        
        if status:
            query = query.filter(Suggestion.status == status)
        
        return query.scalar()
    

