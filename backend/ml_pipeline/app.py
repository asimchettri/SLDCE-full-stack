import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import sqlite3

# ================= PATH SETUP =================
PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_PATH = PROJECT_ROOT / "results"
MEMORY_PATH = PROJECT_ROOT / "memory"
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"

MEMORY_PATH.mkdir(exist_ok=True)

SUGGESTIONS_FILE = RESULTS_PATH / "suggestions.csv"
DB_FILE = MEMORY_PATH / "memory.db"

RAW_TEST_FILE = "adult.csv"

# ================= STREAMLIT CONFIG =================
st.set_page_config(page_title="SLDCE – Human-in-the-Loop UI", layout="wide")
st.title("🧠 SLDCE – Human-in-the-Loop Review System")

# ================= DATABASE SETUP =================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS decisions (
    sample_index INTEGER PRIMARY KEY,
    auto_action TEXT,
    final_action TEXT,
    reason TEXT,
    corrected_label TEXT,
    risk_score REAL,
    anomaly_risk REAL,
    last_updated TEXT
)
""")
conn.commit()

# ================= LOAD SUGGESTIONS =================
if not SUGGESTIONS_FILE.exists():
    st.error("❌ suggestions.csv not found. Run Notebook 06 first.")
    st.stop()

df = pd.read_csv(SUGGESTIONS_FILE)

# ================= LOAD RAW DATA =================
raw_df = None
raw_path = DATA_RAW_PATH / RAW_TEST_FILE
if raw_path.exists():
    raw_df = pd.read_csv(raw_path)
    st.success("✅ Raw data loaded (original features visible)")
else:
    st.warning("⚠️ Raw data not found")

# ================= AUTO DECISION =================
def auto_decide(row):
    risk = row.get("combined_risk_score", 0)
    anomaly = row.get("anomaly_risk", 0)
    pred = row.get("predicted_label")
    label = row.get("label")
    conf = row.get("predicted_label_confidence", 0)

    if risk >= 0.9 and anomaly >= 0.85:
        return "REMOVE", "Extreme risk & anomaly"

    if risk >= 0.75 and pred != label and conf >= 0.8:
        return "CORRECT", "High confidence label mismatch"

    if risk < 0.3:
        return "ACCEPT", "Low risk"

    return "REVIEW", "Needs human judgment"

# Always ensure auto columns exist
df[["auto_action", "auto_reason"]] = df.apply(
    lambda r: pd.Series(auto_decide(r)), axis=1
)

# ================= LOAD EXISTING DECISIONS =================
existing = pd.read_sql("SELECT * FROM decisions", conn)

# 🔑 CRITICAL FIX: ensure final_action column ALWAYS exists
df["final_action"] = df["auto_action"]

if not existing.empty:
    df = df.reset_index().rename(columns={"index": "sample_index"})
    df = df.merge(
        existing[["sample_index", "final_action"]],
        on="sample_index",
        how="left"
    )
    df["final_action"] = df["final_action_y"].fillna(df["final_action_x"])
    df = df.drop(columns=["final_action_x", "final_action_y"]).set_index("sample_index")

# ================= OVERVIEW TABLE =================
st.subheader("📋 All Samples (Editable)")

cols = [
    "combined_risk_score",
    "anomaly_risk",
    "auto_action",
    "auto_reason",
    "final_action",
    "predicted_label",
    "label"
]
cols = [c for c in cols if c in df.columns]

edited_df = st.data_editor(
    df[cols],
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "final_action": st.column_config.SelectboxColumn(
            "Final Action",
            options=["ACCEPT", "CORRECT", "REMOVE", "REVIEW"]
        )
    }
)

# ================= DETAIL PANEL =================
st.markdown("---")
st.subheader("🔍 Detailed Review")

idx = st.selectbox("Select sample index", edited_df.index.tolist())
sample = df.loc[idx]

st.write("**Auto decision:**", sample["auto_action"])
st.write("**Reason:**", sample["auto_reason"])
st.write("**Prediction:**", sample.get("predicted_label"))
st.write("**Label:**", sample.get("label"))

st.markdown("### 🧾 Raw Features")
if raw_df is not None and idx in raw_df.index:
    st.dataframe(raw_df.loc[idx].to_frame("Value"))

# ================= SAVE (UPDATE SAME DB FILE) =================
st.markdown("---")
if st.button("💾 SAVE ALL DECISIONS"):
    now = datetime.now().isoformat()

    for i, row in edited_df.iterrows():
        cur.execute("""
        INSERT INTO decisions (
            sample_index, auto_action, final_action,
            reason, corrected_label, risk_score,
            anomaly_risk, last_updated
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sample_index) DO UPDATE SET
            final_action=excluded.final_action,
            last_updated=excluded.last_updated
        """, (
            int(i),
            df.loc[i, "auto_action"],
            row["final_action"],
            df.loc[i, "auto_reason"],
            df.loc[i, "predicted_label"] if row["final_action"] == "CORRECT" else None,
            df.loc[i].get("combined_risk_score"),
            df.loc[i].get("anomaly_risk"),
            now
        ))

    conn.commit()
    st.success("✅ Decisions saved to memory.db (single modifiable file)")
