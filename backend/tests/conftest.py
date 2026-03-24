"""
conftest.py
-----------
Shared pytest fixtures for SLDCE backend tests.

Uses SQLite in-memory database (no Neon/Postgres required).
Patches engine_registry singleton so each test gets a clean instance
with a temporary store directory.
"""

import json
import tempfile
from pathlib import Path
from typing import Generator, List

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# ── DB setup ────────────────────────────────────────────────────────────────

from models.dataset import Base as DatasetBase, Sample
from models.model import Base as ModelBase

ALL_BASES = [DatasetBase, ModelBase]


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    In-memory SQLite session.
    Creates all tables fresh for every test function.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    for base in ALL_BASES:
        base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        for base in ALL_BASES:
            base.metadata.drop_all(engine)


# ── Sample data helpers ──────────────────────────────────────────────────────

DATASET_ID = 99  # safe ID that won't collide with prod data


def _make_iris_like(n: int = 150, n_features: int = 4, n_classes: int = 3,
                    seed: int = 42) -> tuple:
    """Return (X: ndarray, y: ndarray) similar to Iris."""
    rng = np.random.RandomState(seed)
    X = rng.randn(n, n_features)
    y = (np.arange(n) % n_classes)
    return X, y


@pytest.fixture
def iris_samples(db: Session) -> List[Sample]:
    """
    Insert 150 Iris-like Sample rows into the in-memory DB.
    Returns the list of inserted Sample objects.
    """
    X, y = _make_iris_like()
    samples = []
    for i, (features, label) in enumerate(zip(X.tolist(), y.tolist())):
        s = Sample(
            dataset_id=DATASET_ID,
            sample_index=i,
            features=json.dumps(features),
            original_label=int(label),
            current_label=int(label),
            is_suspicious=False,
            is_corrected=False,
        )
        db.add(s)
        samples.append(s)
    db.commit()
    for s in samples:
        db.refresh(s)
    return samples


@pytest.fixture
def small_df() -> tuple:
    """
    Return (X: pd.DataFrame, y: pd.Series) with 60 rows.
    Enough to fit the engine without triggering the 10-sample guard.
    """
    X_arr, y_arr = _make_iris_like(n=60)
    cols = [f"feature_{i}" for i in range(X_arr.shape[1])]
    X = pd.DataFrame(X_arr, columns=cols)
    y = pd.Series(y_arr.astype(str))   # engine labels can be str or int
    return X, y


# ── Engine registry fixture ──────────────────────────────────────────────────

@pytest.fixture
def tmp_registry(tmp_path, monkeypatch):
    """
    Fresh EngineRegistry backed by a temp directory.
    Resets the module-level singleton so tests are isolated.
    """
    import services.engine_registry as er_module

    registry = er_module.EngineRegistry(store_dir=tmp_path)

    # Reset singleton so get_engine_registry() returns our instance
    monkeypatch.setattr(er_module, "_registry_instance", registry)

    return registry


@pytest.fixture(autouse=True)
def reset_registry_singleton(monkeypatch):
    """
    Auto-used: resets the registry singleton before every test so
    a stale in-memory engine from a previous test can't bleed through.
    """
    import services.engine_registry as er_module
    monkeypatch.setattr(er_module, "_registry_instance", None)