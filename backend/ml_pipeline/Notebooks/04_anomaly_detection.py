#!/usr/bin/env python
# coding: utf-8

# ## Imports & Project Setup

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


# ## Load Config

# In[2]:


# ========== LOAD CONFIG ==========
with open(PROJECT_ROOT / "config/default.yaml", "r") as f:
    config = yaml.safe_load(f)

ANOM_CONTAMINATION = config["signals"]["anomaly_contamination"]

print("Anomaly contamination:", ANOM_CONTAMINATION)


# ## Load Processed Test Data

# In[3]:


# ========== LOAD PROCESSED TEST DATA ==========
test_path = PROJECT_ROOT / "data/processed/dataset_processed_test.csv"
test_df = pd.read_csv(test_path)

X_test = test_df.drop(columns=["label"])

print("Test samples:", X_test.shape)


# ## Train Isolation Forest

# In[4]:


# ========== ISOLATION FOREST ==========
from sklearn.ensemble import IsolationForest

iso_forest = IsolationForest(
    n_estimators=200,
    contamination=ANOM_CONTAMINATION,
    random_state=42
)

iso_forest.fit(X_test)

print("Isolation Forest trained")


# ## Compute Anomaly Scores & Flags

# In[5]:


# ========== ANOMALY SCORES ==========
# decision_function: higher = more normal
raw_scores = iso_forest.decision_function(X_test)

# Convert to anomaly score: higher = more anomalous
anomaly_score = -raw_scores

# Predict outliers (-1 = anomaly, 1 = normal)
anomaly_flag = iso_forest.predict(X_test) == -1

anomaly_df = test_df.copy()
anomaly_df["anomaly_score"] = anomaly_score
anomaly_df["anomaly_flag"] = anomaly_flag

print("Detected anomalies:", anomaly_flag.sum())


# ## save Anomaly Signal

# In[6]:


# ========== SAVE ANOMALY RESULTS ==========
results_path = PROJECT_ROOT / "results"
results_path.mkdir(parents=True, exist_ok=True)

output_path = results_path / "anomaly_results.csv"
anomaly_df.to_csv(output_path, index=False)

print("Anomaly results saved to:", output_path)


# #### Notebook 04 uses an unsupervised Isolation Forest to detect feature-level anomalies. This signal is independent of model predictions and helps identify rare or out-of-distribution samples that may require review

# In[ ]:




