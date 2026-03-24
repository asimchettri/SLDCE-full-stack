# Self-Learning Data Correction Engine

A production-grade, modular Python backend for automatically detecting and
correcting label noise in tabular classification datasets. The engine uses an
ensemble of classifiers, anomaly detectors, and a human-in-the-loop feedback
loop to progressively improve label quality over successive correction cycles.

---

## 1. System Overview

Label noise — incorrectly assigned class labels — degrades model accuracy and
reliability. Manual correction of large datasets is expensive. This engine
automates the _detection_ of suspicious labels using multiple complementary
signals, presents them to a human reviewer with full context, learns from
reviewer decisions, and retrains the ensemble using validated corrections.

The system is designed as a pure Python backend. All outputs are
JSON-serializable dictionaries. A frontend team can wire any API layer
(FastAPI, Flask, etc.) on top of the engine's public methods.

---

## 2. Architecture Diagram

```
                        ┌──────────────────────────────────────┐
                        │        SelfLearningCorrectionEngine  │
                        │              (engine.py)             │
                        └───────────────────┬──────────────────┘
                                            │ orchestrates
              ┌─────────────────────────────┼─────────────────────────────┐
              │                             │                             │
     ┌────────▼────────┐         ┌──────────▼──────────┐     ┌──────────▼──────────┐
     │ DataPreprocessor│         │ EnsembleClassifier  │     │  SignalExtractor     │
     │ (preprocessing) │         │   (ensemble.py)     │     │ (signal_extraction) │
     └────────┬────────┘         └──────────┬──────────┘     └──────────┬──────────┘
              │                             │                             │
     Cleaned  │                  Per-model  │                   Signal   │
     features │                  proba      │                   dicts    │
              └────────────────────┬────────┘                            │
                                   │                                      │
                          ┌────────▼────────┐                            │
                          │SignalVectorBuilder│◄──────────────────────────┘
                          │ (signal_vector) │
                          └────────┬────────┘
                                   │ numeric signal matrix
                          ┌────────▼────────┐
                          │  MetaNoiseModel │
                          │  (meta_model)   │
                          └────────┬────────┘
                                   │ P(noise) per sample
                          ┌────────▼────────┐
                          │DecisionController│
                          │  (decision.py)  │
                          └────────┬────────┘
                                   │ flagged samples
                          ┌────────▼────────┐
                          │ReviewPayloadBuilder│
                          │ (review_builder)│
                          └────────┬────────┘
                                   │ review dict
                              Human Reviewer
                                   │ feedback
                          ┌────────▼────────┐
                          │  FeedbackStore  │
                          │  (feedback.py)  │
                          └────────┬────────┘
                       ┌───────────┼─────────────┐
                       │           │             │
              ┌────────▼──┐ ┌──────▼──────┐ ┌───▼────────────┐
              │MetaNoiseModel│ │Retraining  │ │MetricsComputer │
              │(retrain)  │ │ Manager     │ │ + Analytics    │
              └───────────┘ └─────────────┘ └────────────────┘
```

---

## 3. File Reference

### `preprocessing.py` — DataPreprocessor

**What it does:** Detects numeric and categorical columns automatically from
a DataFrame and builds a ColumnTransformer pipeline with median imputation +
StandardScaler for numeric columns, and most-frequent imputation + OneHotEncoder
for categorical columns.

**Why it exists:** Centralizes all feature engineering so the rest of the system
works on clean, normalized arrays. Separating preprocessing from modeling keeps
each component testable and replaceable.

**Connects to:** `ensemble.py` consumes the `fit_transform` / `transform` output.
`retraining.py` calls `fit_transform` again after corrections are applied.

---

### `ensemble.py` — EnsembleClassifier

**What it does:** Manages three default classifiers (RandomForest,
GradientBoosting, LogisticRegression) plus optional custom models. Exposes
`predict_proba_all` (per-model matrices), `predict_proba_mean` (averaged
probabilities), and `predict` (argmax of mean).

**Why it exists:** Ensemble diversity is the foundation of noise detection.
Where individual models disagree, a label is likely ambiguous or incorrect.
Using three models with different inductive biases maximizes disagreement signal.

**Connects to:** `signal_extraction.py` consumes per-model probabilities.
`retraining.py` calls `fit` again after corrections.

---

### `signal_extraction.py` — SignalExtractor

**What it does:** Computes seven noise signals per sample:
- `max_confidence`: how certain the ensemble is of its top class.
- `entropy`: uncertainty over all classes.
- `margin`: gap between the top-2 predicted probabilities.
- `disagreement`: mean pairwise L2 distance between model probability vectors.
- `isolation_score`: IsolationForest score (higher = more anomalous).
- `lof_score`: LocalOutlierFactor score (higher = more anomalous).
- `centroid_dist`: L2 distance from sample to its predicted class centroid.

**Why it exists:** No single signal reliably identifies all types of noise.
Each signal captures a different aspect: model uncertainty, ensemble consensus,
and distributional anomaly. Together they provide a rich, redundant view.

**Connects to:** `signal_vector.py` converts these dicts to numeric arrays.

---

### `signal_vector.py` — SignalVectorBuilder

**What it does:** Defines a fixed canonical ordering for signal keys and converts
signal dicts into numeric arrays for meta-model consumption.

**Why it exists:** Dict key ordering is not guaranteed to be stable across Python
versions. A fixed canonical order ensures the meta-model always receives a
consistently structured feature vector. New signals must be appended to avoid
invalidating trained meta-models.

**Connects to:** `meta_model.py` receives the output matrices.

---

### `meta_model.py` — MetaNoiseModel

**What it does:** Trains a LogisticRegression classifier to predict
P(label is noisy) from a signal vector. Accumulates (signal_vector, is_noisy)
pairs from human feedback. Retrains only when both classes are present and
minimum sample count is met. Uses StandardScaler for feature normalization.

**Why it exists:** The raw signals are informative but require calibration.
The meta-model learns _which combination of signals predicts noise_ in the
specific domain of the dataset being corrected. It gets smarter with every
feedback cycle.

**The learning process:**
1. `apply_feedback` is called with `decision_type='approve'` → stored as `is_noisy=True`.
2. `apply_feedback` is called with `decision_type='reject'` → stored as `is_noisy=False`.
3. `update_meta_model()` triggers `MetaNoiseModel.train()`.
4. StandardScaler normalizes all signal vectors.
5. LogisticRegression fits on accumulated examples.
6. Subsequent `detect_noise()` calls use the updated model probabilities.

**Connects to:** `feedback.py` provides training labels. `decision.py` consumes predictions.

---

### `decision.py` — DecisionController

**What it does:** Maintains the noise probability threshold and decides which
samples to flag. Adapts the threshold after each review cycle based on correction
precision feedback.

**Threshold adaptation logic:**
- If `correction_precision` decreased vs last cycle → threshold increases by
  `increase_step` (become stricter, flag fewer samples, reduce false positives).
- If `correction_precision` improved or held → threshold decreases by
  `decrease_step` (flag more samples, increase recall).
- Threshold is clamped to `[min_threshold, max_threshold]` at all times.

**Why it exists:** A fixed threshold cannot adapt to different datasets or
reviewers. As the meta-model improves and reviewers provide more feedback,
the threshold should evolve to maintain good precision-recall balance.

**Reasoning:** The asymmetric step sizes (0.05 increase vs 0.02 decrease) reflect
a conservative default: it is safer to be slower at becoming more permissive than
to rapidly over-flag clean samples.

**Connects to:** `meta_model.py` (input probabilities), `analytics.py` (logs threshold history).

---

### `feedback.py` — FeedbackRecord + FeedbackStore

**What it does:** `FeedbackRecord` is an immutable value object capturing the
full context of a single reviewer decision. `FeedbackStore` accumulates all
records and provides query methods (`get_pending_for_retrain`, `count_by_decision`).

**Valid decision types:** `approve` (label was wrong, accept correction),
`reject` (label was correct, reject correction), `modify` (label was wrong,
use a custom correction), `uncertain` (reviewer unsure).

**Why it exists:** Complete feedback provenance enables auditing, meta-model
retraining, and correction metric computation. Separating record creation from
storage keeps each concern isolated and testable.

**Connects to:** `meta_model.py`, `retraining.py`, `metrics.py`.

---

### `metrics.py` — MetricsComputer

**What it does:** Computes two families of metrics:
- **Model metrics:** accuracy, macro/weighted precision, recall, F1, confusion matrix.
- **Correction metrics:** correction_precision, false_correction_rate,
  review_agreement_rate, auto_approval_rate.

**Why it exists:** Separating metric computation into its own module keeps
`engine.py` focused on orchestration and makes metric logic independently testable.

**Connects to:** `analytics.py` receives the computed dicts for history tracking.

---

### `analytics.py` — AnalyticsTracker

**What it does:** Records per-cycle snapshots of all metrics and exposes
longitudinal time series (accuracy history, F1 history, threshold history, etc.)
via `get_analytics()`.

**Why it exists:** Single-cycle metrics do not show whether the system is
improving over time. Analytics history enables dashboard visualization and
regression detection.

**Connects to:** `engine.py` calls `record_cycle()` after each retrain.

---

### `retraining.py` — RetrainingManager

**What it does:** Applies confirmed label corrections to a safe copy of the
dataset and triggers ensemble + preprocessor retraining. Tracks which sample
IDs have already been corrected to avoid double-application. Counts cycles.

**Safety rules:**
1. Never mutates the original DataFrame.
2. Works on deep copies.
3. Only applies corrections from records with `approve` or `modify` decisions.
4. Skips retraining if fewer than `min_corrections_to_retrain` new corrections exist.

**Why it exists:** Data immutability during retraining prevents silent bugs where
the original ground truth is overwritten, making rollback impossible.

**Connects to:** `feedback.py`, `ensemble.py`, `preprocessing.py`.

---

### `review_builder.py` — ReviewPayloadBuilder

**What it does:** Assembles a rich, human-readable dict for a specific sample
containing raw feature values, original and predicted labels, noise probability,
all signal values, and per-model probability distributions.

**Why it exists:** Reviewers need complete context to make confident decisions.
The payload gives everything needed in a single structured response without
requiring the reviewer to query multiple endpoints.

**Connects to:** `engine.py` (called by `generate_review_payload`).

---

### `engine.py` — SelfLearningCorrectionEngine

**What it does:** Top-level orchestrator. Holds all subsystem instances and
wires them together through the public API. Contains no business logic — it
delegates to the appropriate subsystem for each operation.

**Connects to:** All other modules.

---

## 4. Deep Dives

### DecisionController Logic

The DecisionController solves the threshold calibration problem. A static
threshold of 0.5 is arbitrary and does not adapt to:
- How well the meta-model has learned the domain.
- How noisy the dataset actually is.
- How strict or lenient the reviewer team is.

After each review cycle, `update_threshold()` is called with the observed
`correction_precision` (what fraction of flagged samples were confirmed as noisy).
If precision dropped, the engine was over-flagging (too many false positives) →
raise threshold. If precision improved, there is room to catch more → lower threshold.

The asymmetric steps (raise faster than lower) implement a conservative default
that prioritizes reviewer time: better to miss a few noisy labels than to waste
review cycles on clean samples.

### MetaNoiseModel Learning Process

The meta-model is a second-level learner that operates on _signals about signals_.
Rather than looking at raw features, it learns which combinations of model
uncertainty, anomaly scores, and geometric distances predict real label noise.

The learning cycle:
```
Cycle 0: No feedback. All predictions return 0.5 (uniform uncertainty).
Cycle 1: First N reviews collected. If both classes present → first training.
Cycle N: Model has seen hundreds of examples. Predictions become domain-calibrated.
```

The meta-model is intentionally simple (LogisticRegression) because:
- Signal vectors are only 7-dimensional; deep models are overkill.
- Logistic regression is interpretable — coefficients show which signals matter.
- It trains in milliseconds even on thousands of feedback examples.

### Signal Extraction Purpose

Each of the seven signals covers a distinct failure mode:

| Signal | Detects |
|---|---|
| max_confidence | Low-confidence predictions near decision boundaries |
| entropy | Spread uncertainty across many classes |
| margin | Ambiguity between exactly two competing classes |
| disagreement | Cases where models fundamentally disagree |
| isolation_score | Globally unusual feature values |
| lof_score | Locally unusual compared to near neighbors |
| centroid_dist | Far from typical member of predicted class |

A sample flagged by multiple signals is more likely to be genuinely noisy
than one flagged by a single signal.

### Threshold Adaptation Reasoning

The threshold controls the precision-recall tradeoff for the correction process.
High threshold → high precision, low recall (miss some noise). Low threshold →
high recall, low precision (review more clean samples). The adaptive mechanism
finds the right operating point for the specific dataset and reviewer capacity.

### Human-in-the-Loop Workflow

```
1. fit(X, y)              — Initial training
2. detect_noise(X, y)     — Get flagged samples list
3. generate_review_payload(id) — Get full context for one sample
4. apply_feedback(...)    — Record reviewer decision
   (repeat 3-4 for each flagged sample)
5. update_meta_model()    — Retrain noise detector
6. update_threshold()     — Adapt sensitivity
7. retrain_if_ready()     — Retrain ensemble if enough corrections
   (repeat from step 2)
```

---

## 5. Full Training Cycle Step-by-Step

**Step 1 — Initial Fit**
```python
engine.fit(X_train, y_train)
```
- DataPreprocessor detects column types, builds and fits ColumnTransformer.
- EnsembleClassifier trains RandomForest, GradientBoosting, LogisticRegression.
- SignalExtractor fits IsolationForest and LOF on transformed training data.
- Initial model metrics computed and stored.

**Step 2 — Noise Detection**
```python
result = engine.detect_noise(X, y)
```
- Transform X using fitted preprocessor.
- Collect per-model probability matrices from all classifiers.
- Compute all 7 signals per sample.
- Convert to signal matrix.
- MetaNoiseModel predicts P(noise) for each sample.
- DecisionController flags samples above threshold.

**Step 3 — Human Review**
```python
payload = engine.generate_review_payload(sample_id)
# Reviewer examines payload
engine.apply_feedback(sample_id, prev_label, new_label, "approve")
```
- Payload builder assembles full review context.
- Feedback record stored with full signal snapshot and timestamp.
- Meta-model receives (signal_vector, is_noisy) labeled example.

**Step 4 — Meta-Model Update**
```python
engine.update_meta_model()
```
- LogisticRegression retrained on all accumulated feedback.
- Skipped if only one class present or too few examples.

**Step 5 — Threshold Update**
```python
engine.update_threshold()
```
- Correction precision computed from feedback records.
- Threshold raised or lowered based on precision change.

**Step 6 — Ensemble Retraining**
```python
result = engine.retrain_if_ready()
```
- Checks if enough new confirmed corrections exist (default: ≥5).
- Applies corrections to a safe copy of the dataset.
- Refits preprocessor and all ensemble models.
- Refits anomaly detectors on new data.
- Computes and records updated metrics.
- Analytics tracker records cycle snapshot.

---

## 6. Example Usage Script

```python
import pandas as pd
import numpy as np
from sklearn.datasets import load_iris
from engine import SelfLearningCorrectionEngine

# Load a sample dataset
iris = load_iris(as_frame=True)
X = iris.data
y = iris.target

# Inject some artificial label noise (10% flip)
rng = np.random.default_rng(0)
n_flip = int(0.10 * len(y))
flip_idx = rng.choice(len(y), n_flip, replace=False)
for i in flip_idx:
    other_classes = [c for c in y.unique() if c != y.iloc[i]]
    y.iloc[i] = rng.choice(other_classes)

# Initialize engine
engine = SelfLearningCorrectionEngine(
    contamination=0.1,
    initial_threshold=0.5,
    min_corrections_to_retrain=3,
    n_estimators=50,
    random_state=42,
)

# Step 1: Initial training
engine.fit(X, y)
print("Initial metrics:", engine.get_metrics())

# Step 2: Detect noise
result = engine.detect_noise(X, y)
print(f"Flagged {len(result['flagged_samples'])} samples")
print(f"Threshold: {result['current_threshold']}")

# Step 3: Review first flagged sample
if result["flagged_samples"]:
    flagged_id = result["flagged_samples"][0]["sample_id"]
    payload = engine.generate_review_payload(flagged_id)
    print("Review payload:", payload)

    # Simulate reviewer approving the correction
    engine.apply_feedback(
        sample_id=flagged_id,
        previous_label=payload["original_label"],
        updated_label=payload["predicted_label"],
        decision_type="approve",
        reviewer_comment="Label clearly wrong based on feature values.",
        reviewer_confidence=0.95,
    )

# Step 4: Update meta-model and threshold
engine.update_meta_model()
engine.update_threshold()

# Step 5: Retrain if ready
retrain_result = engine.retrain_if_ready()
print("Retrain result:", retrain_result)

# Step 6: Get analytics
analytics = engine.get_analytics()
print("Analytics:", analytics)
```

---

## 7. Configuration Guide

All configuration is passed to `SelfLearningCorrectionEngine.__init__`:

| Parameter | Default | Description |
|---|---|---|
| `custom_models` | `None` | List of additional sklearn classifiers |
| `contamination` | `0.1` | Expected noise fraction for IsolationForest/LOF |
| `initial_threshold` | `0.5` | Starting noise probability cutoff |
| `min_threshold` | `0.2` | Minimum threshold after adaptation |
| `max_threshold` | `0.9` | Maximum threshold after adaptation |
| `threshold_increase_step` | `0.05` | Raise amount when precision drops |
| `threshold_decrease_step` | `0.02` | Lower amount when precision improves |
| `min_corrections_to_retrain` | `5` | Minimum new corrections to trigger retraining |
| `n_estimators` | `100` | Trees for RF and GB |
| `random_state` | `42` | Global random seed |

**Tuning tips:**
- Increase `contamination` for domains known to have high label noise (>15%).
- Lower `initial_threshold` to catch more noise in the first cycle.
- Reduce `min_corrections_to_retrain` for small datasets.
- Increase `n_estimators` for better ensemble diversity at the cost of speed.

---

## 8. Extension Guide

### Adding a New Signal

1. Add the computation logic to `SignalExtractor.compute_signals()` in `signal_extraction.py`.
2. Include the new key in the returned signal dict for every sample.
3. **Append** the new key to `SIGNAL_ORDER` at the end of `signal_vector.py`.
   Do not insert in the middle — this invalidates existing meta-models.
4. Any previously trained meta-model will not use the new signal until retrained.

### Adding a New Model to the Ensemble

```python
from sklearn.svm import SVC
custom_svm = SVC(probability=True, kernel="rbf")

engine = SelfLearningCorrectionEngine(custom_models=[custom_svm])
```

Requirements: model must implement `fit(X, y)` and `predict_proba(X)` returning
shape `(n_samples, n_classes)` with the same class order as `ensemble.classes_`.

### Adding a New Decision Type

1. Add the new string to `VALID_DECISION_TYPES` in `feedback.py`.
2. Update `FeedbackStore.get_pending_for_retrain()` if the new type should
   contribute to retraining.
3. Update `MetricsComputer.compute_correction_metrics()` to count the new type.
4. Update `MetaNoiseModel` feedback logic in `engine.apply_feedback()` if the
   new type has a defined noise label.

---

## 9. Limitations and Risks

**Meta-model cold start:** Until enough feedback is collected (default: 10 samples
with both positive and negative examples), the meta-model returns 0.5 for all
samples. The initial cycles rely entirely on signal magnitude, not learned combinations.

**Contamination parameter sensitivity:** IsolationForest and LOF results depend
heavily on the `contamination` parameter. An incorrect value can generate
misleading anomaly scores. Consider estimating noise fraction from domain knowledge.

**Signal saturation:** If a dataset has very high noise rates (>30%), the class
centroids themselves become corrupted, making `centroid_dist` less reliable.

**LOF novelty mode:** LOF uses `novelty=True` to support `predict` on new data.
This requires that the training data distribution is representative. Significant
distribution shift between fit and inference data will degrade LOF scores.

**Ensemble agreement ≠ correct label:** The ensemble can be confidently wrong,
especially on systematic biases in the original training data. A low noise
probability does not guarantee the label is correct.

**No active learning prioritization:** The engine flags all samples above the
threshold with equal priority. High-value samples (uncertain predictions near
decision boundaries of rare classes) are not prioritized over bulk easy cases.

---

## 10. Production Considerations

**Persistence:** The engine holds all state in memory. For production, serialize
the `EnsembleClassifier`, `DataPreprocessor`, `MetaNoiseModel`, `FeedbackStore`,
and `DecisionController` using `joblib.dump` / `joblib.load`. Implement a
`save(path)` / `load(path)` method on the engine.

**Thread safety:** The engine is not thread-safe. Wrap in a process-level lock
or deploy as a single-process service with a queue for concurrent review submissions.

**Batch feedback:** For high-throughput pipelines, extend `apply_feedback` to
accept a list of feedback records and apply them atomically before triggering
a single meta-model retrain.

**Scalability:** IsolationForest and LOF scale as O(n log n) and O(n²)
respectively. For datasets >500k rows, consider subsampling the fit data for
anomaly detectors or replacing LOF with a scalable approximate KNN implementation.

**Versioning:** When `SIGNAL_ORDER` in `signal_vector.py` changes, increment a
schema version and store it alongside serialized meta-models to detect
incompatibility on load.

**Monitoring:** Log `correction_precision` and `false_correction_rate` per cycle
to a time-series store. A sudden drop in precision or spike in false corrections
signals data distribution drift and requires investigation.

**Reviewer calibration:** Different reviewers have different error rates. Consider
tracking per-reviewer agreement rates and weighting feedback by reviewer
historical reliability before feeding to the meta-model.
