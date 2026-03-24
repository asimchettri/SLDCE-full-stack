"""
Memory API routes
-----------------
Exposes the SelfLearningCorrectionEngine's longitudinal analytics
and threshold controls for each dataset.

Endpoints:
  GET  /memory/{dataset_id}/analytics        — full learning history
  GET  /memory/{dataset_id}/threshold        — current decision threshold
  POST /memory/{dataset_id}/update-threshold — trigger threshold adaptation
  GET  /memory/{dataset_id}/status           — engine registry status
"""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from core.database import get_db
from services.ml_integration import get_analytics, get_engine_status, run_learning_cycle
from services.engine_registry import get_engine_registry

router = APIRouter()


@router.get("/{dataset_id}/analytics")
async def get_engine_analytics(
    dataset_id: int = Path(..., description="Dataset ID"),
):
    """
    Get full longitudinal analytics for a dataset's engine.

    Returns history of:
    - Accuracy per learning cycle
    - F1 score per cycle
    - Decision threshold evolution
    - Correction precision over time
    - Number of samples flagged per cycle
    """
    return get_analytics(dataset_id)


@router.get("/{dataset_id}/threshold")
async def get_current_threshold(
    dataset_id: int = Path(..., description="Dataset ID"),
):
    """
    Get the current decision threshold for a dataset's engine.

    The threshold adapts over time based on correction precision.
    Higher threshold = more conservative flagging.
    """
    registry = get_engine_registry()
    engine = registry.get(dataset_id)

    if engine is None:
        return {
            "dataset_id": dataset_id,
            "threshold": None,
            "fitted": False,
            "message": "No engine found for this dataset. Run detection first."
        }

    return {
        "dataset_id": dataset_id,
        "threshold": engine._decision.current_threshold(),
        "fitted": engine._fitted,
        "feedback_count": engine._meta_model.feedback_count(),
    }


@router.post("/{dataset_id}/update-threshold")
async def trigger_threshold_update(
    dataset_id: int = Path(..., description="Dataset ID"),

):
    """
    Manually trigger a full learning cycle for a dataset.

    Runs:
    1. update_meta_model() — retrain meta-model on all feedback so far
    2. update_threshold()  — adapt decision threshold
    3. retrain_if_ready()  — retrain ensemble if enough corrections exist

    Use this after a batch of feedback has been submitted.
    """
    result = run_learning_cycle(dataset_id)
    return result


@router.get("/{dataset_id}/status")
async def get_engine_registry_status(
    dataset_id: int = Path(..., description="Dataset ID"),
):
    """
    Get registry status for a dataset's engine.

    Shows:
    - Whether engine exists in memory
    - Whether it has been fitted
    - Whether a joblib file exists on disk
    - File path of the persisted engine
    """
    return get_engine_status(dataset_id)