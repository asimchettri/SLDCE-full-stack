#!/usr/bin/env python
# coding: utf-8

# ## Imports & Project Setup
# Sets correct project root
# ✔ Enables imports from src/
# ✔ Confirms Phase 5 output exists
# ✔ Prevents silent downstream errors

# In[2]:


# ========== BASIC IMPORTS ==========
import sys
from pathlib import Path
import yaml
import pandas as pd
import numpy as np

# ========== PROJECT ROOT ==========
PROJECT_ROOT = Path("..").resolve()
sys.path.append(str(PROJECT_ROOT))

print("Project root:", PROJECT_ROOT)
print("Combined signals file exists:",
      (PROJECT_ROOT / "results/combined_signals.csv").exists())


# ## Load Config & Decision Thresholds
# ✔ Loads decision logic from config
# ✔ Keeps decisions configurable & explainable
# ✔ Allows easy tuning for different datasets
# 
# Risk ≥ REJECT_THRESHOLD → ❌ Reject
# Risk between REVIEW_THRESHOLD and REJECT_THRESHOLD → 🔍 Review
# Risk < REVIEW_THRESHOLD → ✅ Keep

# In[4]:


# ========== LOAD CONFIG ==========
with open(PROJECT_ROOT / "config/default.yaml", "r") as f:
    config = yaml.safe_load(f)

# ========== DECISION THRESHOLDS ==========
REJECT_THRESHOLD = config["decision"]["reject_threshold"]

# You can optionally define a review threshold
REVIEW_THRESHOLD = REJECT_THRESHOLD / 2

print("Reject threshold:", REJECT_THRESHOLD)
print("Review threshold:", REVIEW_THRESHOLD)


# ## Load Combined Signals
# ✔ Loads risk scores for all samples
# ✔ Prepares data for decision making
# ✔ Keeps pipeline modular

# In[5]:


# ========== LOAD COMBINED SIGNALS ==========
combined_path = PROJECT_ROOT / "results/combined_signals.csv"
combined_df = pd.read_csv(combined_path)

print("Total samples:", len(combined_df))
combined_df.head()


# ## Generate Suggestions (CORE DECISION LOGIC)
# #### This cell converts the continuous risk score into human-readable actions.
# Converts numbers → decisions
# ✔ Fully rule-based & explainable
# ✔ No ML black box
# 
# Interpretation:
# 
# KEEP → trusted sample
# 
# REVIEW → human-in-the-loop
# 
# REJECT → likely mislabeled / problematic

# In[7]:


# ========== SUGGESTION LOGIC ==========
def generate_suggestion(risk):
    if risk >= REJECT_THRESHOLD:
        return "REJECT"
    elif risk >= REVIEW_THRESHOLD:
        return "REVIEW"
    else:
        return "KEEP"

combined_df["suggestion"] = combined_df["combined_risk_score"].apply(generate_suggestion)

print("Suggestion counts:")
print(combined_df["suggestion"].value_counts())


# ## Add Decision Explanation
# ✔ Makes SLDCE transparent
# ✔ Enables human trust
# ✔ Excellent for thesis & demo
# ✔ Shows why a sample is flagged

# In[8]:


# ========== DECISION EXPLANATION ==========
def explain_decision(row):
    reasons = []

    if row["confidence_flag"]:
        reasons.append("Low confidence in given label")

    if row["anomaly_risk"] >= 0.5:
        reasons.append("Feature anomaly detected")

    if not reasons:
        reasons.append("No strong risk signals")

    return "; ".join(reasons)

combined_df["decision_reason"] = combined_df.apply(explain_decision, axis=1)

combined_df[["combined_risk_score", "suggestion", "decision_reason"]].head()


# ## Save Suggestions Output
# results/
# └── suggestions.csv
# Combined risk score
# 
# Final decision (KEEP / REVIEW / REJECT)
# 
# Human-readable explanation

# In[9]:


# ========== SAVE SUGGESTIONS ==========
results_path = PROJECT_ROOT / "results"
results_path.mkdir(parents=True, exist_ok=True)

output_path = results_path / "suggestions.csv"
combined_df.to_csv(output_path, index=False)

print("Suggestions saved successfully")
print("Saved at:", output_path)


# In[ ]:




