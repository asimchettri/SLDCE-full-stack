#!/usr/bin/env python
# coding: utf-8

# ## Load Data

# In[1]:


import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path("..").resolve()

raw_df = pd.read_csv(PROJECT_ROOT / "data/raw/adult.csv")
memory = pd.read_csv(PROJECT_ROOT / "memory/memory_snapshot.csv")


# ## Apply corrections

# In[2]:


cleaned_df = raw_df.copy()

# Remove samples
remove_ids = memory[memory["final_action"] == "REMOVE"]["sample_index"]
cleaned_df = cleaned_df.drop(index=remove_ids)

# Correct labels
correct_rows = memory[memory["final_action"] == "CORRECT"]
for _, row in correct_rows.iterrows():
    cleaned_df.loc[row["sample_index"], "income"] = row["corrected_label"]

print("Final cleaned dataset size:", len(cleaned_df))


# ## Save cleaned dataset

# In[3]:


out_path = PROJECT_ROOT / "data/cleaned/adult_cleaned.csv"
cleaned_df.to_csv(out_path, index=False)

print("✅ Saved cleaned dataset:", out_path)


# In[ ]:




