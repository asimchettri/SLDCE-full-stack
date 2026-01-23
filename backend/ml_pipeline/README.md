# SLDCE – Self-Learning Data Cleaning Engine

## Overview
SLDCE is a data-centric machine learning framework that improves model reliability by detecting suspicious samples, incorporating human-in-the-loop review, and cleaning datasets before retraining. Instead of blindly tuning models, SLDCE focuses on improving data quality.

## Key Idea
The model does not learn from corrections directly. Human decisions are applied to the dataset, and the model is retrained on the cleaned data. The model always follows the data.
# **IMPORTANT-->“The SLDCE pipeline is fully configuration-driven. To apply it to a new dataset or model, only the configuration file needs to be updated. The notebooks remain unchanged.”**
config/*.yaml
   │
   ▼
Notebook 01
(Config-based data loading & preprocessing)
   │
   ▼
Notebook 02
(Model training from config)
   │
   ▼
Notebook 03–05
(Signal generation & fusion)
   │
   ▼
Notebook 06
(Suggestion engine)
   │
   ▼
app.py
(Human-in-the-loop review)
   │
   ▼
memory_snapshot.csv
(Final human ground truth)
   │
   ▼
Notebook 08
(Apply corrections)
   │
   ▼
Notebook 09
(Retrain & evaluate)

## Human Decisions
- ACCEPT: Sample is valid and label is correct (no change)
- CORRECT: Sample is valid but label is wrong (label is fixed)
- REMOVE: Sample is unreliable (sample removed)
- REVIEW: Requires human judgment (no change until decided)

Only CORRECT and REMOVE modify the dataset.

## Execution Flow
1. Run notebooks 01–06 to train the initial model and generate signals.
2. Run `app.py` to review samples using the human-in-the-loop UI.
3. Save human decisions to SQLite (`memory.db`).
4. Run Notebook 07 to generate a frozen snapshot (`memory_snapshot.csv`).
5. Run Notebook 08 to apply corrections and create a cleaned dataset.
6. Run Notebook 09 to retrain the model and evaluate performance.

## Storage Strategy
- `memory.db` is used only during UI review for safe updates.
- `memory_snapshot.csv` is the final, read-only human ground truth.
- All future tasks use the snapshot CSV.

## Results
- Original model accuracy: **0.8523**
- Accuracy after SLDCE cleaning: **0.8551**
- Improvement: **+0.28%**

The marginal improvement indicates that the dataset was already relatively clean and that SLDCE preserves clean data while correcting only genuine errors.
Since most samples were accepted without modification and no review samples were corrected or removed, the cleaned dataset remained largely similar to the original dataset. Therefore, only a marginal improvement in accuracy was observed.

## Dataset
UCI Adult Income Dataset (`<=50K`, `>50K`)

## Key Conclusion
SLDCE improves data quality first. Model performance improves only when genuine label noise exists. Stability with minimal changes is a correct and desirable outcome.

## Project Status
End-to-end pipeline completed with human-in-the-loop validation and retraining.
