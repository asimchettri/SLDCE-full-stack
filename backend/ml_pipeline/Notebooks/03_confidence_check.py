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
print("Processed data exists:",
      (PROJECT_ROOT / "data/processed").exists())


# ## Load Config & Confidence Threshold
# ✔ Reads confidence threshold from config
# ✔ Makes signal logic configurable
# ✔ Keeps notebook dataset & model agnostic

# In[2]:


# ========== LOAD CONFIG ==========
with open(PROJECT_ROOT / "config/default.yaml", "r") as f:
    config = yaml.safe_load(f)

# ========== CONFIDENCE SETTINGS ==========
CONF_THRESHOLD = config["signals"]["confidence_threshold"]

print("Confidence threshold:", CONF_THRESHOLD)


# ## Load Processed Data & Trained Model Outputs
# ✔ Loads model-ready test data
# ✔ Keeps confidence checks isolated
# ✔ Uses same processed features as training
# 

# In[3]:


# ========== LOAD PROCESSED DATA ==========
train_path = PROJECT_ROOT / "data/processed/dataset_processed_train.csv"
test_path = PROJECT_ROOT / "data/processed/dataset_processed_test.csv"

train_df = pd.read_csv(train_path)
test_df = pd.read_csv(test_path)

X_test = test_df.drop(columns=["label"])
y_test = test_df["label"]

print("Test samples:", len(test_df))


# ## Load & Train Mode
# ✔ Uses same model config as Notebook 02
# ✔ Ensures confidence scores are consistent
# ✔ Keeps notebook self-contained

# In[4]:


# ========== LOAD MODEL CONFIG ==========
MODEL_NAME = config["model"]["name"]
MODEL_PARAMS = config["model"]["params"]

# ========== REDEFINE MODEL FACTORY (SAME AS NOTEBOOK 02) ==========
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

class BaseModel:
    def __init__(self, **params):
        self.params = params
        self.model = None

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)


class RandomForestModel(BaseModel):
    def __init__(self, **params):
        super().__init__(**params)
        self.model = RandomForestClassifier(**params)


class LogisticModel(BaseModel):
    def __init__(self, **params):
        super().__init__(**params)
        self.model = LogisticRegression(max_iter=1000, **params)


class SVMModel(BaseModel):
    def __init__(self, **params):
        super().__init__(**params)
        self.model = SVC(probability=True, **params)


def get_model(model_name, params):
    if model_name == "random_forest":
        return RandomForestModel(**params)
    elif model_name == "logistic":
        return LogisticModel(**params)
    elif model_name == "svm":
        return SVMModel(**params)
    else:
        raise ValueError("Unsupported model")

# ========== TRAIN MODEL ==========
X_train = train_df.drop(columns=["label"])
y_train = train_df["label"]

model = get_model(MODEL_NAME, MODEL_PARAMS)
model.train(X_train, y_train)

print(f"Model '{MODEL_NAME}' trained for confidence analysis")


# ## Compute Confidence Signal
# A sample is flagged if:
# 
# ❗ Model strongly believes another class
# ❗ But the dataset label has low probability
# 
# This suggests:
# 
# Possible mislabel
# 
# Ambiguous sample
# 
# Hard-to-learn data point

# In[7]:


# ========== MODEL PREDICTIONS ==========
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)

# ========== CLASS ORDER FROM MODEL ==========
class_labels = list(model.model.classes_)
print("Model class order:", class_labels)

# ========== CONFIDENCE COMPUTATION ==========
given_label_confidence = []
predicted_label_confidence = []

for i, true_label in enumerate(y_test):
    # Find index of the true label in class list
    true_label_index = class_labels.index(true_label)

    given_label_confidence.append(y_proba[i][true_label_index])
    predicted_label_confidence.append(y_proba[i].max())

# ========== BUILD CONFIDENCE DATAFRAME ==========
confidence_df = test_df.copy()
confidence_df["predicted_label"] = y_pred
confidence_df["given_label_confidence"] = given_label_confidence
confidence_df["predicted_label_confidence"] = predicted_label_confidence

# ========== FLAG SUSPICIOUS SAMPLES ==========
confidence_df["confidence_flag"] = (
    (confidence_df["predicted_label"] != confidence_df["label"]) &
    (confidence_df["given_label_confidence"] < CONF_THRESHOLD)
)

print(
    "Suspicious samples (confidence-based):",
    confidence_df["confidence_flag"].sum()
)


# ## Save Confidence Signal Output

# In[8]:


# ========== SAVE CONFIDENCE SIGNAL ==========
results_path = PROJECT_ROOT / "results"
results_path.mkdir(parents=True, exist_ok=True)

confidence_output_path = results_path / "confidence_flags.csv"
confidence_df.to_csv(confidence_output_path, index=False)

print("Confidence signal saved successfully")
print("Saved at:", confidence_output_path)


# ## results/
# └── confidence_flags.csv
# This file includes:
# Original label
# Model prediction
# Confidence of given label
# Confidence of predicted label
# confidence_flag (True / False)
# #### ✔ Generic data pipeline (Notebook 01)
# #### ✔ Pluggable model training (Notebook 02)
# #### ✔ First SLDCE signal: confidence-based detection (Notebook 03)
# #### ✔ Works with string labels (<=50K, >50K)
# #### ✔ No noise injection

# In[ ]:




