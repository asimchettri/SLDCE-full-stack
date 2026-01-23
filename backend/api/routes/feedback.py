"""
Feedback API routes
CRITICAL: Feedback data feeds Phase 2 memory/learning system
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from schemas.feedback import (
    FeedbackResponse,
    FeedbackWithDetails,
    FeedbackStatsResponse,
    FeedbackPatternResponse,
    FeedbackListResponse
)
from services.feedback_service import FeedbackService
import math

router = APIRouter()


@router.get("/list", response_model=FeedbackListResponse)
async def get_feedback(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    iteration: Optional[int] = Query(None, description="Filter by iteration"),
    action: Optional[str] = Query(None, description="Filter by action: accept, reject, modify"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get feedback with pagination and filters
    
    Returns all human review decisions for analysis.
    """
    offset = (page - 1) * page_size
    
    feedback = FeedbackService.get_feedback(
        db,
        dataset_id=dataset_id,
        iteration=iteration,
        action=action,
        limit=page_size,
        offset=offset
    )
    
    # Get total count
    total = FeedbackService.count_feedback(
        db,
        dataset_id=dataset_id,
        action=action
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return {
        "feedback": feedback,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback_by_id(
    feedback_id: int = Path(..., description="Feedback ID"),
    db: Session = Depends(get_db)
):
    """Get specific feedback by ID"""
    feedback = FeedbackService.get_feedback_by_id(db, feedback_id)
    return feedback


@router.get("/{feedback_id}/details")
async def get_feedback_details(
    feedback_id: int = Path(..., description="Feedback ID"),
    db: Session = Depends(get_db)
):
    """
    Get feedback with full context
    
    Includes suggestion, detection, and sample details.
    """
    result = FeedbackService.get_feedback_with_details(db, feedback_id)
    return result


@router.get("/stats/{dataset_id}", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db)
):
    """
    Get feedback statistics for a dataset
    
    Shows patterns in human review decisions:
    - Total feedback collected
    - Accept/Reject/Modify counts
    - Acceptance rate
    """
    stats = FeedbackService.get_stats(db, dataset_id)

    return stats


@router.get("/patterns/{dataset_id}", response_model=FeedbackPatternResponse)
async def analyze_feedback_patterns(
    dataset_id: int = Path(..., description="Dataset ID"),
    iteration: int = Query(1, description="Iteration number"),
    db: Session = Depends(get_db)
):
    """
    Analyze patterns in human feedback
    
    Phase 2 CRITICAL: This analysis feeds the memory/learning system.
    Shows which suggestions humans accept/reject and why.
    
    Insights:
    - Most accepted/rejected classes
    - Confidence threshold patterns
    - Human agreement with model predictions
    """
    patterns = FeedbackService.get_patterns(db, dataset_id, iteration)
    return patterns


@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int = Path(..., description="Feedback ID"),
    db: Session = Depends(get_db)
):
    """
    Delete feedback (admin only - use with caution)
    
    WARNING: Deleting feedback removes learning data for Phase 2.
    """
    feedback = FeedbackService.get_feedback_by_id(db, feedback_id)
    db.delete(feedback)
    db.commit()
    
    return {"message": "Feedback deleted successfully", "id": feedback_id}