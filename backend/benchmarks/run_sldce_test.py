import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import SessionLocal
from services.benchmark_service import run_sldce_benchmark

db = SessionLocal()
results = run_sldce_benchmark(db, dataset_id=11, iterations=5)
for r in results:
    print(f"Iter {r['iteration']}: acc={r['accuracy']:.4f}, accepted={r['accepted']}, flagged={r['flagged']}")
db.close()