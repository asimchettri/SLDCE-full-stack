SLDCE Integration README

Project Overview
Project Name: Self-Learning Data Correction Engine (SLDCE)
Semester: 8th Semester Academic Project
Team: 2 developers — Dev 1 (ML Engineer) + Dev 2 (Full-Stack)
Stack: FastAPI + PostgreSQL (Neon) + React + TypeScript
The system detects mislabeled samples in classification datasets using an ensemble ML engine, presents correction suggestions to human reviewers, learns from their feedback, and retrains itself progressively.

Repository Structure
project/
├── backend/
│   ├── self_learning_engine/     ← Dev 1's ML engine (NEW)
│   ├── engine_store/             ← Persisted engine files (NEW, auto-generated)
│   ├── ml_pipeline/              ← OLD notebooks (dead code, do not use)
│   ├── api/
│   │   └── routes/
│   │       ├── datasets.py
│   │       ├── detection.py
│   │       ├── suggestions.py
│   │       ├── feedback.py
│   │       ├── corrections.py
│   │       ├── retrain.py
│   │       ├── baseline.py
│   │       └── memory.py         ← NEW
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── dataset.py
│   │   └── model.py
│   ├── schemas/
│   ├── services/
│   │   ├── engine_registry.py    ← NEW
│   │   ├── ml_integration.py     ← REWRITTEN
│   │   ├── detection_service.py  ← UPDATED
│   │   ├── feedback_service.py   ← UPDATED
│   │   ├── retrain_service.py    ← UPDATED
│   │   ├── baseline_service.py   ← UPDATED
│   │   ├── suggestion_service.py ← UPDATED
│   │   ├── correction_service.py ← UPDATED
│   │   └── ...others unchanged
│   ├── main.py                   ← UPDATED
│   └── requirements.txt
└── frontend/
    └── src/
        ├── services/
        │   └── api.ts            ← UPDATED
        ├── types/
        │   ├── feedback.ts       ← UPDATED
        └── └── memory.ts         ← NEW

How To Set Up (New Developer)
Prerequisites

Python 3.10+
Node.js 18+
A Neon PostgreSQL database URL

Backend Setup
bashcd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in `backend/`:
```
DATABASE_URL=your_neon_postgres_url
DEBUG=True
Start the server:
bashuvicorn main:app --reload
Visit http://localhost:8001/docs to see the full API.
Frontend Setup
bashcd frontend
npm install
npm run dev
Visit http://localhost:5173.

The Core Integration — What Changed and Why
The Problem We Solved
Before this integration, the backend had two completely separate ML systems that were incompatible:
OLD system (ml_pipeline/ folder):

Notebook-based proof of concept
backend/services/ml_integration.py called functions like get_model(), detect_confidence_issues(), detect_anomalies() from these notebooks
These functions did not exist in Dev 1's new engine
The backend had never actually talked to Dev 1's production engine

NEW system (self_learning_engine/ folder):

Production-grade engine delivered by Dev 1
Has memory, adaptive thresholds, meta-model learning, feedback loop
Completely different API — fit(), detect_noise(), apply_feedback(), etc.

The integration replaced all calls to the old notebook pipeline with calls to the new engine, across every service file.

What Was Changed — File by File
NEW FILES
backend/self_learning_engine/__init__.py
Makes the engine folder a proper Python package.
pythonfrom self_learning_engine.engine import SelfLearningCorrectionEngine
backend/services/engine_registry.py
The most important new file. Manages one engine instance per dataset.
Key responsibilities:

Creates a fresh engine for a dataset if none exists
Saves engine state to disk using joblib (engine_store/engine_{id}.joblib)
Loads engine from disk on server restart so learning is not lost
Provides per-dataset thread locks to prevent race conditions

Usage in any service:
pythonfrom services.engine_registry import get_engine_registry

registry = get_engine_registry()

with registry.lock(dataset_id):
    engine = registry.get_or_create(dataset_id)
    engine.fit(X, y)
    registry.save(dataset_id)
backend/api/routes/memory.py
New API endpoints to expose the engine's learning analytics:
EndpointPurposeGET /api/v1/memory/{id}/analyticsFull learning historyGET /api/v1/memory/{id}/thresholdCurrent decision thresholdPOST /api/v1/memory/{id}/update-thresholdTrigger learning cycleGET /api/v1/memory/{id}/statusEngine registry status
frontend/src/types/memory.ts
TypeScript types for the new memory endpoints.

REWRITTEN FILES
backend/services/ml_integration.py
Completely deleted and rewritten. Old version imported from notebooks. New version wraps the engine.
Public functions:
FunctionWhat it doesfit_dataset(db, dataset_id)Loads samples, fits enginedetect_noise(db, dataset_id)Runs noise detection, returns flagged samplesapply_feedback(db, dataset_id, ...)Passes human review decision to enginerun_learning_cycle(dataset_id)Runs meta-model update + threshold adapt + retrainget_analytics(dataset_id)Returns engine's longitudinal historyget_ml_integration()Backward compat shim — only kept for baseline_service until Day 3 rewrite
Important — vocabulary mapping. The backend used 'accept' for feedback actions. The engine uses 'approve'. The translation happens in one place inside ml_integration.py:
pythonDECISION_MAP = {
    "accept":  "approve",
    "approve": "approve",
    "reject":  "reject",
    "modify":  "modify",
    "uncertain": "uncertain",
}
Never bypass this. Always go through apply_feedback().

UPDATED FILES
backend/services/detection_service.py
Old: called ml.run_full_detection() from notebook pipeline.
New: calls fit_dataset() then detect_noise() from the engine.
The run_detection() method now:

Calls fit_dataset() to train the engine on all samples
Creates a DB model entry (self_learning_engine type)
Calls detect_noise() to get flagged samples
Saves Detection records from the engine's output

backend/services/retrain_service.py
Old: called get_model() from old notebooks, had an indentation bug.
New: calls run_learning_cycle() which triggers the full self-learning loop.
The retrain now:

Calls run_learning_cycle() — updates meta-model, adapts threshold, retrains ensemble if enough corrections exist
Evaluates performance on test split using engine's ensemble
Falls back to a fresh RandomForest if engine hasn't retrained yet
Saves MLModel and ModelIteration records as before

backend/services/baseline_service.py
Old: called get_model() from old notebooks.
New: uses sklearn directly (RandomForest, LogisticRegression, or SVM).
The baseline is intentionally separate from the engine — it represents clean-data performance before any corrections. The engine takes over after baseline is established.
backend/services/suggestion_service.py
One line changed in update_suggestion_status():
python# Before:
action = 'accept'

# After:
action = 'approve'   ← matches engine vocabulary
backend/services/correction_service.py
One line changed in apply_corrections():
python# Before:
if feedback.action == 'accept':

# After:
if feedback.action == 'approve':
backend/services/feedback_service.py
Action count strings updated in get_stats() and get_patterns():
python# Before:
sum(1 for f in feedback_list if f.action == 'accept')

# After:
sum(1 for f in feedback_list if f.action == 'approve')
backend/schemas/feedback.py
Pattern validator updated:
python# Before:
action: str = Field(..., pattern="^(accept|reject|modify)$")

# After:
action: str = Field(..., pattern="^(approve|reject|modify|uncertain)$")
backend/models/dataset.py
Comment only — no schema change:
pythonaction = Column(String(50), nullable=False)  # 'approve', 'reject', 'modify', 'uncertain'
backend/main.py
Added memory router:
pythonfrom api.routes import ..., memory

app.include_router(memory.router, prefix=f"{settings.API_V1_PREFIX}/memory", tags=["memory"])
frontend/src/types/feedback.ts
typescript// Before:
export type FeedbackAction = 'accept' | 'reject' | 'modify';

// After:
export type FeedbackAction = 'approve' | 'reject' | 'modify' | 'uncertain';
frontend/src/components/FeedbackTimelineItem.tsx
Switch case updated:
typescript// Before:
case 'accept':

// After:
case 'approve':
Display label still shows "Accepted" to users — only the internal value changed.
frontend/src/pages/FeedbackPage.tsx
Filter dropdown value updated:
typescript// Before:
<SelectItem value="accept">Accepted</SelectItem>

// After:
<SelectItem value="approve">Accepted</SelectItem>
frontend/src/services/api.ts
Added memoryAPI object at the bottom:
typescriptexport const memoryAPI = {
  getAnalytics: async (datasetId: number) => {...},
  getThreshold: async (datasetId: number) => {...},
  updateThreshold: async (datasetId: number) => {...},
  getStatus: async (datasetId: number) => {...},
};

Database Migration
One SQL statement was run on Neon to migrate existing test data:
sqlUPDATE feedback SET action = 'approve' WHERE action = 'accept';
```

Run this on any database that has old feedback data with `action = 'accept'`.

---

## The Self-Learning Engine — How It Works

This is Dev 1's engine. As a new developer you don't need to modify it, but you need to understand its lifecycle.

### Engine Lifecycle Per Dataset
```
1. fit(X, y)
   └─ Preprocesses data, trains ensemble (RF + GB + LR),
      fits anomaly detectors (IsolationForest + LOF)

2. detect_noise(X, y)
   └─ Computes 7 signals per sample, runs meta-model,
      returns samples above threshold as "flagged"

3. apply_feedback(sample_id, decision_type, ...)
   └─ Stores FeedbackRecord, feeds signal vector to meta-model
      decision_type: 'approve' | 'reject' | 'modify' | 'uncertain'

4. update_meta_model()
   └─ Retrains LogisticRegression on all feedback so far

5. update_threshold()
   └─ Adapts decision threshold based on correction precision
      (increases threshold if too many false positives)

6. retrain_if_ready()
   └─ If >= 5 confirmed corrections exist, retrains full ensemble
      on corrected dataset
```

### Cold Start Behavior
When a dataset has no feedback yet, the meta-model returns 0.5 for all samples. Detection still works — it uses the initial threshold of 0.5.

### Persistence
Every engine mutation (`fit`, `apply_feedback`, `retrain_if_ready`) is saved to disk immediately by `engine_registry.save(dataset_id)`. File location: `backend/engine_store/engine_{dataset_id}.joblib`.

If the server restarts, the engine is reloaded from disk on the next request. Learning is never lost.

---

## API Flow — End to End

A typical correction cycle looks like this:
```
1. POST /api/v1/datasets/upload
   └─ Upload CSV, creates Dataset + Sample records

2. POST /api/v1/detection/run  { dataset_id: 1 }
   └─ fit_dataset() → detect_noise() → creates Detection records

3. POST /api/v1/suggestions/generate  { dataset_id: 1 }
   └─ Creates Suggestion records from Detection records

4. PATCH /api/v1/suggestions/{id}/status  { status: "accepted" }
   └─ Updates Suggestion → creates Feedback record (action='approve')
   └─ Calls engine.apply_feedback() to feed learning system

5. POST /api/v1/corrections/apply/{dataset_id}
   └─ Updates Sample.current_label based on approved feedback

6. POST /api/v1/retrain/retrain/{dataset_id}
   └─ run_learning_cycle() → update_meta_model → update_threshold
      → retrain_if_ready → saves new MLModel + ModelIteration

7. GET /api/v1/memory/{dataset_id}/analytics
   └─ Returns full learning history for the dataset

Critical Rules For New Developers
Never call the engine directly from a route. Always go through services/ml_integration.py. The registry, locking, and persistence all live there.
Never import from ml_pipeline/. That folder is dead code. Nothing calls it anymore. If you see an import from ml_pipeline it is a bug.
Always use the lock when mutating engine state:
pythonwith registry.lock(dataset_id):
    engine = registry.get_or_create(dataset_id)
    # mutate engine here
    registry.save(dataset_id)
Feedback vocabulary is approve not accept. The DB stores approve. The engine expects approve. The frontend FeedbackAction type is 'approve'. The only place that translates is DECISION_MAP in ml_integration.py.
Suggestion vocabulary stays as-is. Suggestion statuses (accepted/rejected/modified) are separate from feedback actions (approve/reject/modify). The translation from suggestion status to feedback action happens in suggestion_service.update_suggestion_status().
The FeedbackStatsResponse.accepted field stays as accepted. Even though the DB value is now approve, the API response field is still named accepted for display purposes. The count logic in feedback_service.get_stats() handles this by counting rows where action == 'approve' but returning the count under the key accepted.

Verification Commands
Run these after any change to confirm nothing is broken:
bash# From backend/
python -c "from self_learning_engine import SelfLearningCorrectionEngine; print('Engine OK')"
python -c "from services.engine_registry import get_engine_registry; print('Registry OK')"
python -c "from services.ml_integration import fit_dataset, detect_noise, apply_feedback, run_learning_cycle; print('ML Integration OK')"
python -c "from services.detection_service import DetectionService; from services.retrain_service import RetrainService; from services.baseline_service import BaselineService; print('Services OK')"
python -c "from api.routes.memory import router; print('Memory route OK')"

# Start server
uvicorn main:app --reload
# Should end with: Application startup complete.

# From frontend/
npx tsc --noEmit
# Should return with no output (no errors)

What Is Still Left (Future Work)

The ml_pipeline/ folder can be safely deleted once the project is signed off
The _LegacyMLIntegration shim in ml_integration.py can be removed once confirmed nothing depends on it
engine_store/ should be added to .gitignore — joblib files are large binary files
Multi-iteration support: the current flow assumes iteration=1. Future iterations need the engine to be re-fit on corrected data before detecting noise again
The uncertain feedback action is now supported in the schema and engine but the frontend does not yet have a UI button for it — can be added to SuggestionReviewActions.tsx