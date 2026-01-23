import pandas as pd
from pathlib import Path

def load_dataset(path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path.resolve()}")

    if path.suffix == ".csv":
        return pd.read_csv(path)
    elif path.suffix in [".xls", ".xlsx"]:
        return pd.read_excel(path)
    else:
        raise ValueError("Unsupported file format")
