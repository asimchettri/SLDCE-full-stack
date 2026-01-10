"""
Suggestions API routes
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from schemas.suggestion import (
    SuggestionResponse,
    SuggestionWithDetection,
    SuggestionGenerateRequest,
    SuggestionGenerateResponse,
    SuggestionUpdateRequest,
    SuggestionStatsResponse,
    SuggestionListResponse
)
from services.suggestion_service import SuggestionService
import math

router = APIRouter()


@router.post("/generate", response_model=SuggestionGenerateResponse)
async def generate_suggestions(
    request: SuggestionGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate correction suggestions for detected samples
    
    Suggestions are ranked by detection priority score.
    Optionally limit to top N suggestions.
    """
    result = SuggestionService.generate_suggestions(
        db,
        dataset_id=request.dataset_id,
        iteration=request.iteration,
        top_n=request.top_n
    )
    return result


@router.get("/list", response_model=SuggestionListResponse)
async def get_suggestions(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    iteration: Optional[int] = Query(None, description="Filter by iteration"),
    status: Optional[str] = Query(None, description="Filter by status: pending, accepted, rejected, modified"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Minimum confidence score"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get suggestions with pagination and filters
    
    Returns paginated list of suggestions ordered by confidence.
    """
    offset = (page - 1) * page_size
    
    suggestions = SuggestionService.get_suggestions(
        db,
        dataset_id=dataset_id,
        iteration=iteration,
        status=status,
        min_confidence=min_confidence,
        limit=page_size,
        offset=offset
    )
    
    # Get total count
    total = SuggestionService.count_suggestions(
        db,
        dataset_id=dataset_id,
        status=status
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return {
        "suggestions": suggestions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{suggestion_id}", response_model=SuggestionResponse)
async def get_suggestion(
    suggestion_id: int = Path(..., description="Suggestion ID"),
    db: Session = Depends(get_db)
):
    """Get specific suggestion by ID"""
    suggestion = SuggestionService.get_suggestion_by_id(db, suggestion_id)
    return suggestion


@router.get("/{suggestion_id}/details")
async def get_suggestion_details(
    suggestion_id: int = Path(..., description="Suggestion ID"),
    db: Session = Depends(get_db)
):
    """
    Get suggestion with full detection and sample details
    
    Includes:
    - Suggestion information
    - Associated detection scores
    - Sample features and labels
    """
    result = SuggestionService.get_suggestion_with_detection(db, suggestion_id)
    return result


@router.patch("/{suggestion_id}/status", response_model=SuggestionResponse)
async def update_suggestion_status(
    suggestion_id: int = Path(..., description="Suggestion ID"),
    request: SuggestionUpdateRequest = None,
    db: Session = Depends(get_db)
):
    """
    Update suggestion status (for human review/feedback)
    
    Status options:
    - accepted: Human accepted the suggestion
    - rejected: Human rejected the suggestion
    - modified: Human made a different correction (requires custom_label)
    
    Note: Automatically creates Feedback record for Phase 2 learning
    """
    suggestion = SuggestionService.update_suggestion_status(
        db,
        suggestion_id=suggestion_id,
        status=request.status,
        reviewer_notes=request.reviewer_notes,
        custom_label=request.custom_label  # NEW
    )
    return suggestion


@router.get("/stats/{dataset_id}", response_model=SuggestionStatsResponse)
async def get_suggestion_stats(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db)
):
    """
    Get suggestion statistics for a dataset
    
    Returns counts by status and acceptance rate.
    """
    stats = SuggestionService.get_suggestion_stats(db, dataset_id)
    return stats


@router.delete("/{suggestion_id}")
async def delete_suggestion(
    suggestion_id: int = Path(..., description="Suggestion ID"),
    db: Session = Depends(get_db)
):
    """Delete a suggestion (admin only - use with caution)"""
    suggestion = SuggestionService.get_suggestion_by_id(db, suggestion_id)
    db.delete(suggestion)
    db.commit()
    
    return {"message": "Suggestion deleted successfully", "id": suggestion_id}