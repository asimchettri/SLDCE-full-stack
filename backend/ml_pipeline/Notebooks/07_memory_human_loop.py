#!/usr/bin/env python
# coding: utf-8

# In[25]:


import pandas as pd
import sqlite3
from pathlib import Path


# ### in UI , we have use auto select descion so all that samples comes with auto selection, but we have also REVIEW--> THAT MEANS WE HAVE TO MANUALLY LOOK THE SAMPLE FOR EX 
# ### SAMPLE 5 ----> REVIEW SO , WE WILL LOOK TO ALL THE ORGINAL FEATURES 
# age              34
# workclass        Private
# education        HS-grad
# education.num    9
# occupation       Other-service
# marital.status   Divorced
# relationship     Unmarried
# sex              Female
# hours.per.week   45
# capital.gain     0
# capital.loss     3770
# native.country   United-States
# income           <=50K   (dataset label)
# 
# ### 1️⃣ Does the data itself look valid?
# 
# Ask:
# 
# Any impossible values? ❌ No
# 
# Any missing values? ❌ No
# 
# Any contradictions? ❌ No
# 
# ✔ Data is realistic and consistent
# 
# 👉 So DO NOT REMOVE.
# 
# ### 2️⃣ Is the dataset label reasonable?
#   income <=50K
# 
# Check against human logic:
# 
# Age 34 → early/mid career
# 
# Education: HS-grad (not college)
# 
# Occupation: Other-service (typically low/moderate pay)
# 
# Work hours: 45/week (normal)
# 
# Capital gain: 0
# 
# Capital loss: 3770 (one-time event, not income)
# 
# 🧠 Human reasoning:
# 
# This profile strongly matches <=50K income
# 
# ✔ Label looks correct
# 
# ### 3️⃣ Could the model be right instead?
# 
# If the model predicted >50K, ask:
# 
# Does this person have high-paying signals? ❌ No
# 
# Advanced education? ❌ No
# 
# High capital gains? ❌ No
# 
# 👉 Model prediction >50K would be unlikely
# 
# ### 4️⃣ Final human decision
# ### ✅ BEST ACTION: ACCEPT
# Why?
# 
# Data is valid
# 
# Label makes sense
# 
# No reason to correct
# 
# No reason to remove

# In[26]:


PROJECT_ROOT = Path("..").resolve()

DB_PATH = PROJECT_ROOT / "memory" / "memory.db"
SNAPSHOT_PATH = PROJECT_ROOT / "memory" / "memory_snapshot.csv"

conn = sqlite3.connect(DB_PATH)

memory_df = pd.read_sql("SELECT * FROM decisions", conn)

print("Total raw decision rows:", len(memory_df))
memory_df.head()


# In[27]:


memory_latest = (
    memory_df
    .sort_values("last_updated")
    .groupby("sample_index", as_index=False)
    .last()
)

print("Final reviewed samples:", len(memory_latest))
memory_latest.head()


# In[28]:


memory_df["final_action"].value_counts()


# In[29]:


memory_latest.to_csv(SNAPSHOT_PATH, index=False)

print("✅ Final memory snapshot saved to:")
print(SNAPSHOT_PATH)


# In[ ]:




