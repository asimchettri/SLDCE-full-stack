"""
Data loading utilities extracted from Notebook 01
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder


def load_dataset(file_path: Path) -> pd.DataFrame:
    """
    Load dataset from CSV/Excel file
    
    Args:
        file_path: Path to dataset file
        
    Returns:
        DataFrame with loaded data
    """
    file_ext = file_path.suffix.lower()
    
    if file_ext == '.csv':
        return pd.read_csv(file_path)
    elif file_ext in ['.xls', '.xlsx']:
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


def split_data(
    df: pd.DataFrame,
    target_column: str,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into train/test sets with stratification
    
    Args:
        df: Input DataFrame
        target_column: Name of target column
        test_size: Proportion of test set
        random_state: Random seed
        
    Returns:
        X_train, X_test, y_train, y_test
    """
    X = df.drop(columns=[target_column])
    y = df[target_column]
    
    return train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )


def create_preprocessor(
    numeric_cols: list,
    categorical_cols: list
) -> ColumnTransformer:
    """
    Create preprocessing pipeline
    
    Args:
        numeric_cols: List of numeric column names
        categorical_cols: List of categorical column names
        
    Returns:
        ColumnTransformer for preprocessing
    """
    # Numeric pipeline
    numeric_pipeline = Pipeline(steps=[
        ("scaler", StandardScaler())
    ])
    
    # Categorical pipeline
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
    
    return preprocessor


def identify_feature_types(
    df: pd.DataFrame,
    target_column: str
) -> Tuple[list, list]:
    """
    Identify numeric and categorical columns
    
    Args:
        df: Input DataFrame
        target_column: Name of target column to exclude
        
    Returns:
        (numeric_cols, categorical_cols)
    """
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Identify feature types
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
    
    # Remove target from features
    if target_column in numeric_cols:
        numeric_cols.remove(target_column)
    
    if target_column in categorical_cols:
        categorical_cols.remove(target_column)
    
    return numeric_cols, categorical_cols