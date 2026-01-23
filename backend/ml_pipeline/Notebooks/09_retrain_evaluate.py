#!/usr/bin/env python
# coding: utf-8

# ## Imports & Paths

# In[1]:


import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier


# ## Load Cleaned Dataset

# In[2]:


PROJECT_ROOT = Path("..").resolve()

cleaned_df = pd.read_csv(PROJECT_ROOT / "data/cleaned/adult_cleaned.csv")

print("Cleaned dataset shape:", cleaned_df.shape)
cleaned_df.head()


# ## Separate Features & Target

# In[3]:


TARGET = "income"

X = cleaned_df.drop(columns=[TARGET])
y = cleaned_df[TARGET]


# ## Identify Numeric & Categorical Columns

# In[4]:


numeric_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()

print("Numeric features:", numeric_cols)
print("Categorical features:", categorical_cols)


# ## Train/Test Split

# In[5]:


X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# ## Preprocessing Pipeline

# In[6]:


numeric_pipeline = Pipeline(
    steps=[("scaler", StandardScaler())]
)

categorical_pipeline = Pipeline(
    steps=[("encoder", OneHotEncoder(handle_unknown="ignore"))]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_pipeline, numeric_cols),
        ("cat", categorical_pipeline, categorical_cols)
    ]
)


# ## Model (Same as Original)

# In[8]:


model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)


# ## Full Training Pipeline

# In[9]:


clf = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)

clf


# ## Train Model on Cleaned Data

# In[10]:


clf.fit(X_train, y_train)


# ## EvaEvaluate model

# In[12]:


y_pred = clf.predict(X_test)

acc = accuracy_score(y_test, y_pred)
print("✅ Accuracy on CLEANED data:", round(acc, 4))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))


# ## Compare With Original Accuracy

# In[14]:


original_accuracy = 0.8522954091816367   # replace with your actual value
cleaned_accuracy = acc

print("Original accuracy:", original_accuracy)
print("After SLDCE accuracy:", round(cleaned_accuracy, 4))
print("Improvement:", round(cleaned_accuracy - original_accuracy, 4))


# ## "Since most samples were accepted without modification and no review samples were corrected or removed, the cleaned dataset remained largely similar to the original dataset. Therefore, only a marginal improvement in accuracy was observed.”

# In[ ]:




