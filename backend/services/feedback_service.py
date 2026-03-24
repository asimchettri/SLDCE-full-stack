"""
Feedback service - Business logic for human feedback
FIXED: Added missing get_stats and other methods
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.dataset import Feedback, Suggestion, Detection, Sample
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime


class FeedbackService:
    """Service class for feedback operations"""
    
    @staticmethod
    def create_feedback_from_suggestion(
        db: Session,
        suggestion: Any,
        action: str,
        final_label: int
    ) -> Any:
        detection = db.query(Detection).filter(
            Detection.id == suggestion.detection_id
        ).first()

        if not detection:
            raise HTTPException(status_code=404, detail="Associated detection not found")

        existing = db.query(Feedback).filter(
            Feedback.suggestion_id == suggestion.id
        ).first()

        if existing:
            existing.action = action
            existing.final_label = final_label
            db.commit()
            db.refresh(existing)
            # Also update engine's in-memory feedback store
            FeedbackService._sync_feedback_to_engine(
                db, detection, action, final_label, existing.sample_id
            )
            return existing

        feedback = Feedback(
            suggestion_id=suggestion.id,
            sample_id=detection.sample_id,
            action=action,
            final_label=final_label,
            iteration=detection.iteration
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        # Sync to engine's in-memory feedback store
        FeedbackService._sync_feedback_to_engine(
            db, detection, action, final_label, feedback.sample_id
        )

        return feedback

    @staticmethod
    def _sync_feedback_to_engine(
        db: Session,
        detection: Any,
        action: str,
        final_label: int,
        sample_id: int,
    ) -> None:
        """Push feedback to the engine's in-memory FeedbackStore."""
        try:
            from services.ml_integration import apply_feedback
            from models.dataset import Sample

            sample = db.query(Sample).filter(Sample.id == sample_id).first()
            if sample is None:
                return

            # Find dataset_id via sample
            dataset_id = sample.dataset_id

            apply_feedback(
                db=db,
                dataset_id=dataset_id,
                sample_id=sample_id,
                previous_label=sample.current_label,
                updated_label=final_label,
                decision_type=action,
            )
        except Exception as e:
            # Non-fatal: DB feedback is already saved; engine sync failure
            # only affects in-memory learning, not data integrity
            import logging
            logging.getLogger(__name__).warning(
                f"Engine feedback sync failed (non-fatal): {e}"
            )
    
    @staticmethod
    def get_feedback(
        db: Session,
        dataset_id: Optional[int] = None,
        iteration: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Feedback]:
        query = db.query(Feedback)

        # Only join Sample when filtering by dataset_id
        if dataset_id is not None:
            query = query.join(Sample, Feedback.sample_id == Sample.id)
            query = query.filter(Sample.dataset_id == dataset_id)

        if iteration is not None:
            query = query.filter(Feedback.iteration == iteration)

        if action is not None:
            query = query.filter(Feedback.action == action)

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
    def get_stats(db: Session, dataset_id: int) -> Dict[str, Any]:
        """
        Get feedback statistics for a dataset
        
        Returns:
            Dict with counts and percentages of each action type
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
                "accepted": 0,
                "rejected": 0,
                "modified": 0,
                "acceptance_rate": 0.0
            }
        
        # Count by action
        accepted = sum(1 for f in feedback_list if f.action == 'approve')
        rejected = sum(1 for f in feedback_list if f.action == 'reject')
        modified = sum(1 for f in feedback_list if f.action == 'modify')
        
        # Calculate acceptance rate (accepted + modified = positive outcomes)
        acceptance_rate = ((accepted + modified) / total * 100) if total > 0 else 0.0
        
        return {
            "dataset_id": dataset_id,
            "total_feedback": total,
            "accepted": accepted,
            "rejected": rejected,
            "modified": modified,
            "acceptance_rate": round(acceptance_rate, 2)
        }
    
    @staticmethod
    def get_patterns(
        db: Session,
        dataset_id: int,
        iteration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze feedback patterns for Phase 2 learning
        
        This will be used by the memory system to learn:
        - Which types of detections are accepted/rejected
        - Optimal thresholds
        - Class-specific patterns
        """
        # Get feedback with detection context
        query = db.query(Feedback, Detection, Suggestion).join(
            Suggestion, Feedback.suggestion_id == Suggestion.id
        ).join(
            Detection, Suggestion.detection_id == Detection.id
        ).join(
            Sample, Feedback.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id
        )
        
        if iteration:
            query = query.filter(Feedback.iteration == iteration)
        
        results = query.all()
        
        if not results:
            return {
                "dataset_id": dataset_id,
                "patterns_found": 0,
                "message": "No feedback available for pattern analysis"
            }
        
        # Analyze patterns
        acceptance_by_confidence = {}
        acceptance_by_priority = {}
        
        
        for feedback, detection, suggestion in results:
            # Group by confidence ranges
            conf_range = f"{int(detection.confidence_score * 10) * 10}%"
            if conf_range not in acceptance_by_confidence:
                acceptance_by_confidence[conf_range] = {'total': 0, 'accepted': 0}
            
            acceptance_by_confidence[conf_range]['total'] += 1
            if feedback.action in ['approve', 'modify']:
                acceptance_by_confidence[conf_range]['accepted'] += 1
            
            # Group by priority ranges
            priority_range = "high" if detection.priority_score >= 0.7 else "medium" if detection.priority_score >= 0.4 else "low"
            if priority_range not in acceptance_by_priority:
                acceptance_by_priority[priority_range] = {'total': 0, 'accepted': 0}
            
            acceptance_by_priority[priority_range]['total'] += 1
            if feedback.action in ['approve', 'modify']:
                acceptance_by_priority[priority_range]['accepted'] += 1
        
        # Calculate acceptance rates
        for range_data in acceptance_by_confidence.values():
            range_data['acceptance_rate'] = round(
                (range_data['accepted'] / range_data['total'] * 100) if range_data['total'] > 0 else 0,
                2
            )
        
        for range_data in acceptance_by_priority.values():
            range_data['acceptance_rate'] = round(
                (range_data['accepted'] / range_data['total'] * 100) if range_data['total'] > 0 else 0,
                2
            )
        
        return {
            "dataset_id": dataset_id,
            "iteration": iteration,
            "patterns_found": len(results),
            "acceptance_by_confidence": acceptance_by_confidence,
            "acceptance_by_priority": acceptance_by_priority,
            "insights": FeedbackService._generate_insights(
                acceptance_by_confidence,
                acceptance_by_priority
            )
        }
    
    @staticmethod
    def _generate_insights(
        conf_patterns: Dict,
        priority_patterns: Dict
    ) -> List[str]:
        """Generate human-readable insights from patterns"""
        insights = []
        
        # Find best confidence range
        if conf_patterns:
            best_conf = max(
                conf_patterns.items(),
                key=lambda x: x[1]['acceptance_rate']
            )
            insights.append(
                f"Highest acceptance rate ({best_conf[1]['acceptance_rate']:.0f}%) at {best_conf[0]} confidence"
            )
        
        # Priority insights
        if 'high' in priority_patterns:
            high_rate = priority_patterns['high']['acceptance_rate']
            insights.append(
                f"High priority detections accepted {high_rate:.0f}% of the time"
            )
        
        return insights
    
    @staticmethod
    def count_feedback(
        db: Session,
        dataset_id: Optional[int] = None,
        iteration: Optional[int] = None,
        action: Optional[str] = None,
    ) -> int:
        """Count feedback with filters. Only joins Sample when dataset_id is needed."""
        query = db.query(func.count(Feedback.id))

        if dataset_id is not None:
            query = query.join(Sample, Feedback.sample_id == Sample.id)
            query = query.filter(Sample.dataset_id == dataset_id)

        if iteration is not None:
            query = query.filter(Feedback.iteration == iteration)

        if action is not None:
            query = query.filter(Feedback.action == action)

        return query.scalar()
    
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
            Detection.id == suggestion.detection_id
        ).first()
        
        # Get sample
        sample = db.query(Sample).filter(
            Sample.id == feedback.sample_id
        ).first()
        
        import json
        
        return {
            "feedback_id": feedback.id,
            "action": feedback.action,
            "final_label": feedback.final_label,
            "iteration": feedback.iteration,
            "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
            "suggestion": {
                "id": suggestion.id,
                "suggested_label": suggestion.suggested_label,
                "confidence": suggestion.confidence,
                "reason": suggestion.reason,
                "status": suggestion.status
            },
            "detection": {
                "id": detection.id,
                "confidence_score": detection.confidence_score,
                "anomaly_score": detection.anomaly_score,
                "priority_score": detection.priority_score,
                "predicted_label": detection.predicted_label
            },
            "sample": {
                "id": sample.id,
                "original_label": sample.original_label,
                "current_label": sample.current_label,
                "features": json.loads(sample.features)
            }
        }
    


    @staticmethod
    def delete_feedback(db: Session, feedback_id: int) -> None:
        """Delete feedback record. WARNING: removes learning data."""
        feedback = FeedbackService.get_feedback_by_id(db, feedback_id)
        db.delete(feedback)
        db.commit()    