"""
Benchmark API routes
--------------------
Endpoints for running and retrieving benchmark comparisons
between SLDCE, Cleanlab, random correction, and no-correction baselines.
"""
from fastapi import APIRouter, Depends, Path, Query, BackgroundTasks , HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from core.database import get_db
from services.benchmark_service import (
    get_benchmark_results,
    run_cleanlab_benchmark,
    run_no_correction_benchmark,
    run_random_benchmark,
    run_sldce_benchmark,
)

router = APIRouter()




@router.post("/run/{dataset_id}")
async def run_full_benchmark(
    dataset_id: int = Path(..., description="Dataset ID"),
    iterations: int = Query(5, ge=1, le=10, description="SLDCE iterations to run"),
    db: Session = Depends(get_db),
):
    """
    Run a full benchmark comparison for a dataset.

    Runs all 4 tools in sequence:
    1. no_correction — train on raw noisy data
    2. random        — randomly flag and correct 15% of samples
    3. cleanlab      — find and remove label issues
    4. sldce         — run full iterative correction loop

    Stores all results in benchmark_results table.
    Returns combined results for all tools.
    """
    results = {}

    # 1. No correction baseline
    results["no_correction"] = run_no_correction_benchmark(db, dataset_id)

    # 2. Random correction baseline
    results["random"] = run_random_benchmark(db, dataset_id)

    # 3. Cleanlab
    try:
        results["cleanlab"] = run_cleanlab_benchmark(db, dataset_id)
    except Exception as e:
        results["cleanlab"] = {"error": str(e)}

    # 4. SLDCE
    results["sldce"] = run_sldce_benchmark(db, dataset_id, iterations=iterations)

    return {
        "dataset_id": dataset_id,
        "iterations": iterations,
        "results": results,
    }


@router.post("/run/{dataset_id}/no-correction")
async def run_no_correction(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db),
):
    """Run only the no-correction baseline."""
    return run_no_correction_benchmark(db, dataset_id)


@router.post("/run/{dataset_id}/random")
async def run_random(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db),
):
    """Run only the random correction baseline."""
    return run_random_benchmark(db, dataset_id)


@router.post("/run/{dataset_id}/cleanlab")
async def run_cleanlab(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db),
):
    """Run only the Cleanlab benchmark."""
    return run_cleanlab_benchmark(db, dataset_id)


@router.post("/run/{dataset_id}/sldce")
async def run_sldce(
    dataset_id: int = Path(..., description="Dataset ID"),
    iterations: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    """Run only the SLDCE benchmark."""
    return run_sldce_benchmark(db, dataset_id, iterations=iterations)


@router.get("/export/{dataset_id}")
def export_benchmark_csv(dataset_id: int, db: Session = Depends(get_db)):
    """Export benchmark comparison table as CSV."""
    import csv
    import io
    from fastapi.responses import StreamingResponse

    results = get_benchmark_results(db, dataset_id)
    if not results:
        raise HTTPException(status_code=404, detail="No benchmark results found")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "tool", "iteration", "accuracy", "precision",
        "recall", "f1", "human_effort", "flagged", "accepted"
    ])

    for r in results:
        meta = r.get("meta") or {}
        writer.writerow([
            r["tool"],
            r["iteration"],
            round((r["accuracy"] or 0) * 100, 2),
            round((r["precision"] or 0) * 100, 2),
            round((r["recall"] or 0) * 100, 2),
            round((r["f1"] or 0) * 100, 2),
            r.get("human_effort") or 0,
            meta.get("flagged", ""),
            meta.get("accepted", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=benchmark_results_{dataset_id}.csv"
        },
    )


@router.get("/{dataset_id}", response_model=List[Dict[str, Any]])
async def get_benchmarks(
    dataset_id: int = Path(..., description="Dataset ID"),
    db: Session = Depends(get_db),
):
    """Get all stored benchmark results for a dataset."""
    return get_benchmark_results(db, dataset_id)