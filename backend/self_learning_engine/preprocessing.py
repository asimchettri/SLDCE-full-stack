"""
preprocessing.py
----------------
Handles automatic detection of column types and builds a sklearn Pipeline
with ColumnTransformer for imputation, encoding, and scaling.

Connects to: ensemble.py (provides the preprocessing pipeline used in model training).
"""

import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from typing import Tuple, List


class DataPreprocessor:
    """
    Automatically detects numeric and categorical columns from a DataFrame
    and constructs a ColumnTransformer pipeline for preprocessing.

    Numeric columns: median imputation + standard scaling.
    Categorical columns: most-frequent imputation + one-hot encoding (handle_unknown='ignore').

    Attributes
    ----------
    numeric_cols : List[str]
        Column names detected as numeric.
    categorical_cols : List[str]
        Column names detected as categorical (object/category dtype).
    pipeline : ColumnTransformer
        Fitted sklearn ColumnTransformer.
    """

    def __init__(self) -> None:
        self.numeric_cols: List[str] = []
        self.categorical_cols: List[str] = []
        self.pipeline: ColumnTransformer = None

    def detect_column_types(self, X: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """
        Detect numeric and categorical columns from a DataFrame.

        Parameters
        ----------
        X : pd.DataFrame
            Input feature DataFrame.

        Returns
        -------
        Tuple[List[str], List[str]]
            (numeric_columns, categorical_columns)
        """
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
        return numeric_cols, categorical_cols

    def build_pipeline(self, X: pd.DataFrame) -> ColumnTransformer:
        """
        Build an unfitted ColumnTransformer pipeline based on detected column types.

        Parameters
        ----------
        X : pd.DataFrame
            Input feature DataFrame used to detect column types.

        Returns
        -------
        ColumnTransformer
            Assembled preprocessing pipeline (not yet fitted).
        """
        self.numeric_cols, self.categorical_cols = self.detect_column_types(X)

        numeric_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])

        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ])

        transformers = []
        if self.numeric_cols:
            transformers.append(("num", numeric_pipeline, self.numeric_cols))
        if self.categorical_cols:
            transformers.append(("cat", categorical_pipeline, self.categorical_cols))

        self.pipeline = ColumnTransformer(transformers=transformers, remainder="drop")
        return self.pipeline

    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Build, fit, and transform the input DataFrame.

        Parameters
        ----------
        X : pd.DataFrame

        Returns
        -------
        np.ndarray
            Transformed feature matrix.
        """
        self.build_pipeline(X)
        return self.pipeline.fit_transform(X)

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Apply the already-fitted pipeline to new data.

        Parameters
        ----------
        X : pd.DataFrame

        Returns
        -------
        np.ndarray
        """
        if self.pipeline is None:
            raise RuntimeError("Pipeline not fitted. Call fit_transform first.")
        return self.pipeline.transform(X)
