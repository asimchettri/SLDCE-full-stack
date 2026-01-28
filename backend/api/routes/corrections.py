"""
Correction API routes
Apply corrections from feedback and export cleaned datasets
"""
from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from core.database import get_db
import os
from services.correction_service import CorrectionService
from schemas.correction import (
    CorrectionApplyResponse,
    CorrectionSummaryResponse,
    CorrectionExportResponse,
    CorrectionPreviewResponse
)

router = APIRouter()


@router.post("/apply/{dataset_id}")
async def apply_corrections(
    dataset_id: int = Path(..., description="Dataset ID"),
    iteration: int = Query(1, description="Iteration number"),
    db: Session = Depends(get_db)
):
    """
    Apply all accepted feedback corrections to dataset
    
    Updates sample labels based on human feedback decisions.
    This is a critical step before retraining the model.
    
    Workflow:
    1. Gets all feedback for the dataset/iteration
    2. Updates current_label for accepted/modified suggestions
    3. Marks samples as corrected
    
    Returns statistics about corrections applied.
    """
    result = CorrectionService.apply_corrections(db, dataset_id, iteration)
    return result


@router.get("/preview/{dataset_id}", response_model=CorrectionPreviewResponse)
async def preview_corrections(
    dataset_id: int = Path(..., description="Dataset ID"),
    iteration: int = Query(1, description="Iteration number"),
    db: Session = Depends(get_db)
):
    """
    Preview corrections before applying
        
    Useful for:
    - Verifying feedback before committing
    - Understanding correction impact
    - Quality assurance
    """
    from models.dataset import Feedback, Sample
    
    # Get all feedback for this dataset
    feedback_list = db.query(Feedback).join(
        Sample, Feedback.sample_id == Sample.id
    ).filter(
        Sample.dataset_id == dataset_id,
        Feedback.iteration == iteration
    ).all()
    
    if not feedback_list:
        return {
            "dataset_id": dataset_id,
            "iteration": iteration,
            "total_changes": 0,
            "total_feedback": 0,
            "corrections_to_apply": 0,
            "labels_to_change": 0,
            "samples_to_reject": 0,
            "estimated_noise_reduction": 0.0,
            "changes":[]
        }
    
    # Count what would happen
    corrections_to_apply = 0
    labels_to_change = 0
    samples_to_reject = 0
    changes=[]
    
    
    for feedback in feedback_list:
        sample = db.query(Sample).filter(Sample.id == feedback.sample_id).first()
        if not sample:
            continue
        
        if feedback.action in ['accept', 'modify']:
            corrections_to_apply += 1
            if sample.current_label != feedback.final_label:
                labels_to_change += 1
                changes.append({
                    "sample_id": sample.id,
                    "old_label": sample.current_label,
                    "new_label": feedback.final_label,
                    "action": feedback.action
                })
        elif feedback.action == 'reject':
            samples_to_reject += 1
    
    # Calculate estimated noise reduction
    total_samples = db.query(Sample).filter(
        Sample.dataset_id == dataset_id
    ).count()
    
    estimated_noise_reduction = (
        (labels_to_change / total_samples * 100) if total_samples > 0 else 0
    )
    
    return {
        "dataset_id": dataset_id,
        "iteration": iteration,
        "total_changes": labels_to_change,
        "total_feedback": len(feedback_list),
        "corrections_to_apply": corrections_to_apply,
        "labels_to_change": labels_to_change,
        "samples_to_reject": samples_to_reject,
        "estimated_noise_reduction": round(estimated_noise_reduction, 2),
        "changes": changes
    }


@router.post("/export/{dataset_id}")
async def export_cleaned_dataset(
    dataset_id: int = Path(..., description="Dataset ID"),
    output_dir: str = Query("cleaned_datasets", description="Output directory"),
    db: Session = Depends(get_db)
):
    """
    Export cleaned dataset to CSV file
    
    Creates a CSV file with corrected labels based on applied feedback.
    Useful for:
    - Downloading the cleaned dataset
    - Using the dataset in external tools
    - Archiving correction results
    
    Returns file path and export statistics.
    """
    result = CorrectionService.export_cleaned_dataset(db, dataset_id, output_dir)
    return result


@router.get("/summary/{dataset_id}")
async def get_correction_summary(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db)
):
    """
    Get summary of corrections applied to dataset
    
    Shows:
    - Total samples corrected
    - Labels changed
    - Before/after label distribution
    - Correction rate
    """
    summary = CorrectionService.get_correction_summary(db, dataset_id)
    return summary


@router.get("/download/{dataset_id}")
async def download_cleaned_dataset(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db)
):
    """
    Download cleaned dataset as CSV
    
    Returns the CSV file directly for download
    """
    from fastapi.responses import FileResponse
    import tempfile
    
    # Export to temp file
    result = CorrectionService.export_cleaned_dataset(db, dataset_id, tempfile.gettempdir())
    
    # Return as downloadable file
    return FileResponse(
        path=result['file_path'],
        filename=os.path.basename(result['file_path']),
        media_type='text/csv',
        headers={
            "Content-Disposition": f"attachment; filename={os.path.basename(result['file_path'])}"
        }
    )