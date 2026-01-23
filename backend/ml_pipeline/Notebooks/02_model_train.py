#!/usr/bin/env python
# coding: utf-8

# ## Imports & Project Setup
# ✔ Sets correct project root
# ✔ Allows importing from src/
# ✔ Verifies processed data is available
# ✔ Prevents path-related bugs early

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
print("Processed data folder exists:",
      (PROJECT_ROOT / "data/processed").exists())


# ## Load Config & Model Selection
# ✔ Reads model choice from config (no hardcoding)
# ✔ Makes the notebook model-agnostic
# ✔ Allows switching models by editing YAML only

# In[2]:


# ========== LOAD CONFIG ==========
with open(PROJECT_ROOT / "config/default.yaml", "r") as f:
    config = yaml.safe_load(f)

# ========== MODEL CONFIG ==========
MODEL_NAME = config["model"]["name"]
MODEL_PARAMS = config["model"]["params"]

print("Selected model:", MODEL_NAME)
print("Model parameters:", MODEL_PARAMS)


# ## Load Processed Train & Test Data
# ✔ Loads model-ready data
# ✔ No preprocessing here (already done in Notebook 01)
# ✔ Keeps pipeline modular and clean

# In[3]:


# ========== LOAD PROCESSED DATA ==========
train_path = PROJECT_ROOT / "data/processed/dataset_processed_train.csv"
test_path = PROJECT_ROOT / "data/processed/dataset_processed_test.csv"

train_df = pd.read_csv(train_path)
test_df = pd.read_csv(test_path)

print("Train shape:", train_df.shape)
print("Test shape:", test_df.shape)

train_df.head()


# ## Separate Features & Labels
# ✔ Clean separation of inputs and targets
# ✔ Required for any ML model
# ✔ Keeps later signal computations simple

# In[4]:


# ========== SPLIT FEATURES & LABEL ==========
X_train = train_df.drop(columns=["label"])
y_train = train_df["label"]

X_test = test_df.drop(columns=["label"])
y_test = test_df["label"]

print("X_train:", X_train.shape)
print("y_train:", y_train.shape)
print("X_test:", X_test.shape)
print("y_test:", y_test.shape)


# ## Define BaseModel
# ✔ Forces all models to behave the same
# ✔ Enables easy model swapping
# ✔ Required for confidence-based signals later
# ✔ Clean software-engineering design

# In[5]:


# ========== BASE MODEL (ABSTRACT CONTRACT) ==========
from abc import ABC, abstractmethod

class BaseModel(ABC):
    def __init__(self, **params):
        self.params = params
        self.model = None

    @abstractmethod
    def train(self, X, y):
        pass

    @abstractmethod
    def predict(self, X):
        pass

    @abstractmethod
    def predict_proba(self, X):
        pass


# ## Implement Models + Model Factory
# ✔ Any model can be added later
# ✔ Config controls everything
# ✔ No notebook rewrites needed
# ✔ Fully reusable engine logic

# In[7]:


# ========== MODEL IMPLEMENTATIONS ==========
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

class RandomForestModel(BaseModel):
    def __init__(self, **params):
        super().__init__(**params)
        self.model = RandomForestClassifier(**params)

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)


class LogisticModel(BaseModel):
    def __init__(self, **params):
        super().__init__(**params)
        self.model = LogisticRegression(max_iter=1000, **params)

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)


class SVMModel(BaseModel):
    def __init__(self, **params):
        super().__init__(**params)
        self.model = SVC(probability=True, **params)

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)


# ========== MODEL FACTORY ==========
def get_model(model_name, params):
    if model_name == "random_forest":
        return RandomForestModel(**params)
    elif model_name == "logistic":
        return LogisticModel(**params)
    elif model_name == "svm":
        return SVMModel(**params)
    else:
        raise ValueError(f"Unsupported model: {model_name}")


# ## Train Model & Evaluate Performance
# ✔ Trains the selected model
# ✔ Uses same code for any model
# ✔ Evaluates performance (baseline)
# ✔ Confirms data + model are correct

# In[8]:


# ========== CREATE MODEL ==========
model = get_model(MODEL_NAME, MODEL_PARAMS)

# ========== TRAIN MODEL ==========
model.train(X_train, y_train)

print(f"Model '{MODEL_NAME}' trained successfully")

# ========== PREDICTIONS ==========
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)

# ========== EVALUATION ==========
from sklearn.metrics import accuracy_score, classification_report

accuracy = accuracy_score(y_test, y_pred)
print("Accuracy:", accuracy)

print("\nClassification Report:")
print(classification_report(y_test, y_pred))


# ### Notebook 02 establishes a pluggable model training framework. The model choice is controlled via configuration, enabling SLDCE to operate independently of the underlying classifier.

# In[ ]:




