#!/usr/bin/env python
# coding: utf-8

# # SLDCE – Notebook 01: Config-Driven Data Loading
# ### This notebook loads and standardizes any dataset using configuration only.
# 

# ## Imports

# ## Imports & Project Root
# ✔ Notebook can access src/, config/, data/
# ✔ No fragile ../ path guessing
# ✔ Works for any dataset, any OS
# ✔ Immediately tells you if folder structure is wrong

# In[12]:


# ========== BASIC IMPORTS ==========
import sys
from pathlib import Path
import yaml
import pandas as pd

# ========== ADD PROJECT ROOT TO PATH ==========
PROJECT_ROOT = Path("..").resolve()
sys.path.append(str(PROJECT_ROOT))

# ========== SANITY CHECK ==========
print("Project root:", PROJECT_ROOT)
print("Config exists:", (PROJECT_ROOT / "config/default.yaml").exists())
print("Raw data exists:", (PROJECT_ROOT / "data/raw").exists())


# ## Load Configuration
# ✔ Loads only from config (no hardcoding)
# ✔ Makes pipeline dataset-agnostic
# ✔ Central control for dataset + target
# ✔ Safe for any future dataset

# In[13]:


# ========== LOAD CONFIG ==========
with open(PROJECT_ROOT / "config/default.yaml", "r") as f:
    config = yaml.safe_load(f)

# ========== READ DATASET CONFIG ==========
DATA_PATH = config["dataset"]["path"]
TARGET = config["dataset"]["target_column"]

print("Dataset path:", DATA_PATH)
print("Target column:", TARGET)


# ## Load Dataset
# ✔ Works for CSV / XLS / XLSX
# ✔ Uses project-root–anchored paths
# ✔ No hardcoded filenames
# ✔ Fails early if file is missing (good!)

# In[14]:


# ========== LOAD DATASET ==========
from src.data.loader import load_dataset

df = load_dataset(PROJECT_ROOT / DATA_PATH)

# ========== BASIC VIEW ==========
print("Dataset loaded successfully")
print("Shape:", df.shape)

df.head()


# ## Dataset Sanity Checks
# ✔ Confirms all column names
# ✔ Detects missing values early
# ✔ Verifies target column correctness
# ✔ Prevents silent bugs later

# In[15]:


# ========== BASIC DATASET CHECKS ==========
print("Columns:")
print(df.columns.tolist())

print("\nMissing values per column:")
print(df.isnull().sum())

print("\nTarget distribution:")
print(df[TARGET].value_counts())


# ## Feature Type Detection
# ✔ Does not assume target type
# ✔ Works for any dataset
# ✔ Safe even if target is categorical
# ✔ No .drop() → no KeyError

# In[16]:


# ========== CLEAN COLUMN NAMES ==========
df.columns = df.columns.str.strip()

# ========== IDENTIFY FEATURE TYPES ==========
numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

# ========== REMOVE TARGET SAFELY ==========
if TARGET in numeric_cols:
    numeric_cols.remove(TARGET)

if TARGET in categorical_cols:
    categorical_cols.remove(TARGET)

print("Numeric columns:", numeric_cols)
print("Categorical columns:", categorical_cols)


# ## Preprocessing Pipeline
# ✔ Works for any dataset
# ✔ Handles unseen categories safely
# ✔ No data leakage (fit later, not here)
# ✔ Fully reusable for future datasets

# In[18]:


# ========== PREPROCESSING PIPELINE ==========
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# Numeric features
numeric_pipeline = Pipeline(steps=[
    ("scaler", StandardScaler())
])

# Categorical features
try:
    # sklearn >= 1.2
    categorical_pipeline = Pipeline(steps=[
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
except TypeError:
    # sklearn < 1.2
    categorical_pipeline = Pipeline(steps=[
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse=False))
    ])

# Combine pipelines
preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_pipeline, numeric_cols),
        ("cat", categorical_pipeline, categorical_cols)
    ],
    remainder="drop"
)

print("Preprocessing pipeline created successfully")


# ## Train / Test Split
# ✔ Stratified split (important for income imbalance)
# ✔ Controlled by config (dataset-agnostic)
# ✔ No preprocessing applied yet (no leakage)

# In[19]:


# ========== TRAIN / TEST SPLIT ==========
from src.data.splitter import split_data

X_train, X_test, y_train, y_test = split_data(
    df,
    TARGET,
    test_size=config["preprocessing"]["test_size"],
    random_state=config["preprocessing"]["random_state"]
)

print("Train size:", X_train.shape)
print("Test size:", X_test.shape)


# ## Fit Preprocessor & Save Processed Data
# ✔ Data loaded
# ✔ Config-driven
# ✔ Generic preprocessing
# ✔ Works for any dataset

# In[20]:


# ========== FIT PREPROCESSOR ==========
X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

# ========== CONVERT TO DATAFRAME ==========
train_df = pd.DataFrame(X_train_processed)
train_df["label"] = y_train.values

test_df = pd.DataFrame(X_test_processed)
test_df["label"] = y_test.values

# ========== SAVE PROCESSED DATA ==========
processed_path = PROJECT_ROOT / "data/processed"
processed_path.mkdir(parents=True, exist_ok=True)

train_df.to_csv(processed_path / "dataset_processed_train.csv", index=False)
test_df.to_csv(processed_path / "dataset_processed_test.csv", index=False)

print("Processed data saved successfully")
print("Train processed shape:", train_df.shape)
print("Test processed shape:", test_df.shape)


# In[ ]:




