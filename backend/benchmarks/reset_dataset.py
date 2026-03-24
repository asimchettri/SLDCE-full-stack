# backend/benchmarks/reset_dataset.py
"""
Deletes dataset 1 and all related data so we can re-upload fresh.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import SessionLocal
from models.dataset import Dataset, Sample, Detection, Suggestion, Feedback, BenchmarkResult
from models.model import MLModel, ModelIteration

db = SessionLocal()

DATASET_ID = 1

# Delete in dependency order
deleted = {}
deleted['benchmark_results'] = db.query(BenchmarkResult).filter(BenchmarkResult.dataset_id == DATASET_ID).delete()

# Get all sample IDs first
sample_ids = [s.id for s in db.query(Sample.id).filter(Sample.dataset_id == DATASET_ID).all()]

if sample_ids:
    # Get detection IDs
    detection_ids = [d.id for d in db.query(Detection.id).filter(Detection.sample_id.in_(sample_ids)).all()]

    if detection_ids:
        # Get suggestion IDs
        suggestion_ids = [s.id for s in db.query(Suggestion.id).filter(Suggestion.detection_id.in_(detection_ids)).all()]
        if suggestion_ids:
            deleted['feedback'] = db.query(Feedback).filter(Feedback.suggestion_id.in_(suggestion_ids)).delete(synchronize_session=False)
            deleted['suggestions'] = db.query(Suggestion).filter(Suggestion.id.in_(suggestion_ids)).delete(synchronize_session=False)

        deleted['detections'] = db.query(Detection).filter(Detection.id.in_(detection_ids)).delete(synchronize_session=False)

    deleted['samples'] = db.query(Sample).filter(Sample.dataset_id == DATASET_ID).delete()

# Delete models
deleted['model_iterations'] = db.query(ModelIteration).filter(ModelIteration.dataset_id == DATASET_ID).delete()
deleted['models'] = db.query(MLModel).filter(MLModel.dataset_id == DATASET_ID).delete()

# Soft delete dataset
dataset = db.query(Dataset).filter(Dataset.id == DATASET_ID).first()
if dataset:
    dataset.is_active = False
    deleted['dataset'] = 1

db.commit()
db.close()

print("Reset complete:")
for k, v in deleted.items():
    print(f"  {k}: {v} deleted")
print("\nNow re-upload iris_noisy_15pct.csv via the frontend or API.")