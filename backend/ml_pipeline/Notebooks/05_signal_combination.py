#!/usr/bin/env python
# coding: utf-8

# ## Imports & Project Setup
# ✔ Sets project root
# ✔ Enables imports
# ✔ Confirms previous notebooks produced outputs
# ✔ Fails early if something is missing

# In[1]:


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
print("Results folder exists:",
      (PROJECT_ROOT / "results").exists())


# ## Load Config
# ✔ Reads fusion logic from config
# ✔ Allows tuning without code changes
# ✔ Keeps SLDCE configurable

# In[2]:


# ========== LOAD CONFIG ==========
with open(PROJECT_ROOT / "config/default.yaml", "r") as f:
    config = yaml.safe_load(f)

CONF_W = config["fusion"]["confidence_weight"]
ANOM_W = config["fusion"]["anomaly_weight"]

print("Confidence weight:", CONF_W)
print("Anomaly weight:", ANOM_W)
print("Weight sum:", CONF_W + ANOM_W)


# ## Load Signal Outputs
# ✔ Loads outputs from Notebook 03 & 04
# ✔ Keeps notebooks decoupled
# ✔ Prepares for fusion

# In[5]:


# ========== LOAD SIGNAL FILES ==========
confidence_path = PROJECT_ROOT / "results/confidence_flags.csv"
anomaly_path = PROJECT_ROOT / "results/anomaly_results.csv"

confidence_df = pd.read_csv(confidence_path)
anomaly_df = pd.read_csv(anomaly_path)

print("Confidence signals shape:", confidence_df.shape)
print("Anomaly signals shape:", anomaly_df.shape)

confidence_df.head()


# ## Align & Validate Signals
# ✔ Prevents silent misalignment bugs
# ✔ Ensures correct signal fusion
# ✔ Critical for trustworthy correction decisions
# 
# In SLDCE, misaligned signals = wrong decisions, so this check is mandatory

# In[6]:


# ========== BASIC VALIDATION ==========
assert len(confidence_df) == len(anomaly_df), \
    "Mismatch between confidence and anomaly signal lengths"

print("Signal alignment check passed")

# We will build combined results on top of confidence_df
combined_df = confidence_df.copy()


# ## Normalize Individual Signals (Risk Scores)
# We convert different signals into comparable [0,1] risk values.
# 
# ✔ Converts heterogeneous signals into a common scale
# ✔ Enables weighted fusion
# ✔ Keeps logic model-agnostic & dataset-agnostic
# 
# You can explain this as:
# 
# “Before combining signals, SLDCE normalizes each signal into a unified risk representation, ensuring fair contribution during fusion.”

# In[8]:


# ========== CONFIDENCE RISK ==========
# Binary signal → already normalized
combined_df["confidence_risk"] = combined_df["confidence_flag"].astype(int)

# ========== ANOMALY RISK ==========
# Higher anomaly_score = more anomalous
anom_scores = anomaly_df["anomaly_score"]

# Min–max normalization
anom_norm = (anom_scores - anom_scores.min()) / (
    anom_scores.max() - anom_scores.min() + 1e-8
)

combined_df["anomaly_risk"] = anom_norm

print("Confidence risk stats:")
print(combined_df["confidence_risk"].value_counts())

print("\nAnomaly risk stats:")
print(combined_df["anomaly_risk"].describe())


# ## Weighted Signal Fusion (CORE LOGIC)
# ✔ Combines independent signals
# ✔ Produces a continuous risk score
# ✔ Fully config-driven
# ✔ Model & dataset agnostic

# In[9]:


# ========== WEIGHTED SIGNAL FUSION ==========
combined_df["combined_risk_score"] = (
    CONF_W * combined_df["confidence_risk"] +
    ANOM_W * combined_df["anomaly_risk"]
)

print("Combined risk score statistics:")
print(combined_df["combined_risk_score"].describe())


# ## Save Combined Signals
# results/
# 
#    └── combined_signals.csv
# This file contains:
# confidence_flag
# confidence_risk
# anomaly_risk
# combined_risk_score ← 🔑 key output of Phase 5

# In[10]:


# ========== SAVE COMBINED SIGNALS ==========
results_path = PROJECT_ROOT / "results"
results_path.mkdir(parents=True, exist_ok=True)

output_path = results_path / "combined_signals.csv"
combined_df.to_csv(output_path, index=False)

print("Combined signals saved successfully")
print("Saved at:", output_path)


# In[ ]:




