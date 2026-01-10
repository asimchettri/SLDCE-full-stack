"""
Feedback service - Business logic for human feedback collection
CRITICAL: This data feeds the memory/learning system in Phase 2
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.dataset import Sample, Detection, Suggestion, Feedback
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import math


class FeedbackService:
    """Service class for feedback operations"""
    
    @staticmethod
    def create_feedback_from_suggestion(
        db: Session,
        suggestion: Suggestion,
        action: str,
        final_label: int
    ) -> Feedback:
        """
        Create feedback record from suggestion review
        
        This is automatically called when a suggestion status is updated.
        Feedback data is CRITICAL for Phase 2 memory/learning system.
        """
        
        # Get associated detection and sample
        detection = db.query(Detection).filter(
            Detection.id == suggestion.detection_id
        ).first()
        
        if not detection:
            raise HTTPException(status_code=404, detail="Associated detection not found")
        
        sample = db.query(Sample).filter(Sample.id == detection.sample_id).first()
        
        if not sample:
            raise HTTPException(status_code=404, detail="Associated sample not found")
        
        # Check if feedback already exists for this suggestion
        existing_feedback = db.query(Feedback).filter(
            Feedback.suggestion_id == suggestion.id
        ).first()
        
        if existing_feedback:
            # Update existing feedback instead of creating duplicate
            existing_feedback.action = action
            existing_feedback.final_label = final_label
            db.commit()
            db.refresh(existing_feedback)
            return existing_feedback
        
        # Create new feedback record
        feedback = Feedback(
            suggestion_id=suggestion.id,
            sample_id=sample.id,
            action=action,
            final_label=final_label,
            iteration=detection.iteration,
            review_time_seconds=None  # Not tracking time in Phase 1
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        return feedback
    
    @staticmethod
    def get_feedback(
        db: Session,
        dataset_id: Optional[int] = None,
        iteration: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Feedback]:
        """Get feedback with optional filters"""
        
        query = db.query(Feedback)
        
        # Join with Sample for dataset filtering
        if dataset_id:
            query = query.join(Sample, Feedback.sample_id == Sample.id)
            query = query.filter(Sample.dataset_id == dataset_id)
        
        # Apply filters
        if iteration:
            query = query.filter(Feedback.iteration == iteration)
        
        if action:
            query = query.filter(Feedback.action == action)
        
        # Order by most recent first
        query = query.order_by(Feedback.created_at.desc())
        
        return query.offset(offset).limit(limit).all()
    
    @staticmethod
    def get_feedback_by_id(db: Session, feedback_id: int) -> Feedback:
        """Get specific feedback by ID"""
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        return feedback
    
    @staticmethod
    def get_feedback_with_details(
        db: Session,
        feedback_id: int
    ) -> Dict[str, Any]:
        """Get feedback with full context (suggestion, detection, sample)"""
        
        feedback = FeedbackService.get_feedback_by_id(db, feedback_id)
        
        # Get suggestion
        suggestion = db.query(Suggestion).filter(
            Suggestion.id == feedback.suggestion_id
        ).first()
        
        # Get detection
        detection = db.query(Detection).filter(
            Detection.id == suggestion.detection_id if suggestion else None
        ).first()
        
        # Get sample
        sample = db.query(Sample).filter(Sample.id == feedback.sample_id).first()
        
        return {
            "feedback_id": feedback.id,
            "suggestion_id": feedback.suggestion_id,
            "sample_id": feedback.sample_id,
            "action": feedback.action,
            "final_label": feedback.final_label,
            "iteration": feedback.iteration,
            "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
            "current_label": sample.current_label if sample else None,
            "suggested_label": suggestion.suggested_label if suggestion else None,
            "original_label": sample.original_label if sample else None,
            "confidence_score": suggestion.confidence if suggestion else None,
            "detection_info": {
                "confidence_score": detection.confidence_score,
                "anomaly_score": detection.anomaly_score,
                "priority_score": detection.priority_score
            } if detection else None
        }
    
    @staticmethod
    def get_feedback_stats(db: Session, dataset_id: int) -> Dict[str, Any]:
        """
        Get feedback statistics for a dataset
        
        This provides insights into human review patterns.
        Phase 2: Used by memory system to learn optimal thresholds.
        """
        
        # Get all feedback for this dataset
        feedback_list = db.query(Feedback).join(
            Sample, Feedback.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id
        ).all()
        
        total = len(feedback_list)
        
        if total == 0:
            return {
                "dataset_id": dataset_id,
                "total_feedback": 0,
                "accept_count": 0,
                "reject_count": 0,
                "modify_count": 0,
                "acceptance_rate": 0.0,
                "avg_review_time": None
            }
        
        # Count by action
        accept_count = sum(1 for f in feedback_list if f.action == 'accept')
        reject_count = sum(1 for f in feedback_list if f.action == 'reject')
        modify_count = sum(1 for f in feedback_list if f.action == 'modify')
        
        # Calculate acceptance rate (accept + modify = positive)
        acceptance_rate = ((accept_count + modify_count) / total * 100) if total > 0 else 0.0
        
        # Average review time (if tracked)
        review_times = [f.review_time_seconds for f in feedback_list if f.review_time_seconds]
        avg_review_time = sum(review_times) / len(review_times) if review_times else None
        
        return {
            "dataset_id": dataset_id,
            "total_feedback": total,
            "accept_count": accept_count,
            "reject_count": reject_count,
            "modify_count": modify_count,
            "acceptance_rate": round(acceptance_rate, 2),
            "avg_review_time": round(avg_review_time, 2) if avg_review_time else None
        }
    
    @staticmethod
    def analyze_feedback_patterns(
        db: Session,
        dataset_id: int,
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Analyze patterns in human feedback
        
        Phase 2: This analysis feeds the memory/learning system
        - Which classes get accepted more?
        - Do high confidence suggestions get accepted more?
        - What's the threshold where humans start rejecting?
        """
        
        # Get all feedback with associated data
        feedback_with_suggestions = db.query(
            Feedback, Suggestion, Detection, Sample
        ).join(
            Suggestion, Feedback.suggestion_id == Suggestion.id
        ).join(
            Detection, Suggestion.detection_id == Detection.id
        ).join(
            Sample, Feedback.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id,
            Feedback.iteration == iteration
        ).all()
        
        if not feedback_with_suggestions:
            return {
                "dataset_id": dataset_id,
                "iteration": iteration,
                "most_accepted_class": None,
                "most_rejected_class": None,
                "high_confidence_acceptance_rate": 0.0,
                "low_confidence_acceptance_rate": 0.0
            }
        
        # Analyze by suggested class
        class_acceptances: Dict[int, int] = {}
        class_rejections: Dict[int, int] = {}
        
        high_conf_accepted = 0
        high_conf_total = 0
        low_conf_accepted = 0
        low_conf_total = 0
        
        for feedback, suggestion, detection, sample in feedback_with_suggestions:
            suggested_class = suggestion.suggested_label
            
            # Track by class
            if feedback.action in ['accept', 'modify']:
                class_acceptances[suggested_class] = class_acceptances.get(suggested_class, 0) + 1
            elif feedback.action == 'reject':
                class_rejections[suggested_class] = class_rejections.get(suggested_class, 0) + 1
            
            # Track by confidence threshold
            if suggestion.confidence >= 0.8:  # High confidence
                high_conf_total += 1
                if feedback.action in ['accept', 'modify']:
                    high_conf_accepted += 1
            else:  # Low confidence
                low_conf_total += 1
                if feedback.action in ['accept', 'modify']:
                    low_conf_accepted += 1
        
        # Find most accepted/rejected classes
        most_accepted_class = max(class_acceptances.items(), key=lambda x: x[1])[0] if class_acceptances else None
        most_rejected_class = max(class_rejections.items(), key=lambda x: x[1])[0] if class_rejections else None
        
        # Calculate acceptance rates by confidence
        high_conf_rate = (high_conf_accepted / high_conf_total * 100) if high_conf_total > 0 else 0.0
        low_conf_rate = (low_conf_accepted / low_conf_total * 100) if low_conf_total > 0 else 0.0
        
        return {
            "dataset_id": dataset_id,
            "iteration": iteration,
            "most_accepted_class": most_accepted_class,
            "most_rejected_class": most_rejected_class,
            "high_confidence_acceptance_rate": round(high_conf_rate, 2),
            "low_confidence_acceptance_rate": round(low_conf_rate, 2)
        }
    
    @staticmethod
    def count_feedback(
        db: Session,
        dataset_id: Optional[int] = None,
        action: Optional[str] = None
    ) -> int:
        """Count feedback with filters"""
        query = db.query(func.count(Feedback.id))
        
        if dataset_id:
            query = query.join(Sample, Feedback.sample_id == Sample.id)
            query = query.filter(Sample.dataset_id == dataset_id)
        
        if action:
            query = query.filter(Feedback.action == action)
        
        return query.scalar()