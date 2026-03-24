"""
test_engine_registry.py
-----------------------
Unit tests for services/engine_registry.py

Tests:
  - test_get_or_create_returns_new_engine
  - test_save_and_reload_persists_engine
  - test_lock_prevents_race_condition
"""

import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from self_learning_engine import SelfLearningCorrectionEngine
from services.engine_registry import EngineRegistry, get_engine_registry


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_fitted_engine() -> SelfLearningCorrectionEngine:
    """Return an engine that has been fit on minimal data."""
    rng = np.random.RandomState(0)
    X = pd.DataFrame(rng.randn(60, 4), columns=[f"f{i}" for i in range(4)])
    y = pd.Series((np.arange(60) % 3).astype(str))
    engine = SelfLearningCorrectionEngine()
    engine.fit(X, y)
    return engine


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestGetOrCreate:
    def test_get_or_create_returns_new_engine(self, tmp_registry: EngineRegistry):
        """
        get_or_create() for an unseen dataset_id must return a fresh
        SelfLearningCorrectionEngine that has NOT been fitted yet.
        """
        engine = tmp_registry.get_or_create(dataset_id=1)

        assert isinstance(engine, SelfLearningCorrectionEngine)
        assert engine._fitted is False

    def test_get_or_create_returns_same_instance_on_second_call(
        self, tmp_registry: EngineRegistry
    ):
        """
        Calling get_or_create() twice with the same dataset_id must return
        the identical in-memory object (no re-instantiation).
        """
        e1 = tmp_registry.get_or_create(dataset_id=2)
        e2 = tmp_registry.get_or_create(dataset_id=2)

        assert e1 is e2

    def test_get_or_create_different_ids_return_different_engines(
        self, tmp_registry: EngineRegistry
    ):
        """Each dataset_id must get its own independent engine."""
        e1 = tmp_registry.get_or_create(dataset_id=10)
        e2 = tmp_registry.get_or_create(dataset_id=11)

        assert e1 is not e2

    def test_get_returns_none_for_unknown_dataset(self, tmp_registry: EngineRegistry):
        """
        get() (non-creating variant) must return None when no engine
        has been created or saved for that dataset_id.
        """
        result = tmp_registry.get(dataset_id=999)

        assert result is None

    def test_is_fitted_false_before_fit(self, tmp_registry: EngineRegistry):
        """is_fitted() must return False for a freshly created engine."""
        tmp_registry.get_or_create(dataset_id=3)

        assert tmp_registry.is_fitted(dataset_id=3) is False

    def test_is_fitted_true_after_fit(self, tmp_registry: EngineRegistry):
        """is_fitted() must return True once the engine has been fit."""
        engine = tmp_registry.get_or_create(dataset_id=4)
        rng = np.random.RandomState(1)
        X = pd.DataFrame(rng.randn(60, 4), columns=[f"f{i}" for i in range(4)])
        y = pd.Series((np.arange(60) % 3).astype(str))
        engine.fit(X, y)

        assert tmp_registry.is_fitted(dataset_id=4) is True


class TestSaveAndReload:
    def test_save_and_reload_persists_engine(self, tmp_path: Path):
        """
        save() writes a joblib file; a new EngineRegistry pointed at the
        same directory must load the engine from disk and restore _fitted state.
        """
        # Registry A: create, fit, save
        registry_a = EngineRegistry(store_dir=tmp_path)
        engine_a = registry_a.get_or_create(dataset_id=5)

        rng = np.random.RandomState(2)
        X = pd.DataFrame(rng.randn(60, 4), columns=[f"f{i}" for i in range(4)])
        y = pd.Series((np.arange(60) % 3).astype(str))
        engine_a.fit(X, y)
        saved = registry_a.save(dataset_id=5)

        assert saved is True
        assert (tmp_path / "engine_5.joblib").exists()

        # Registry B: cold start, load from disk
        registry_b = EngineRegistry(store_dir=tmp_path)
        engine_b = registry_b.get_or_create(dataset_id=5)

        assert engine_b._fitted is True

    def test_save_returns_false_when_engine_not_in_memory(
        self, tmp_registry: EngineRegistry
    ):
        """save() must return False if no engine exists for that dataset_id."""
        result = tmp_registry.save(dataset_id=777)

        assert result is False

    def test_delete_removes_file_and_memory(self, tmp_path: Path):
        """delete() must remove the engine from memory and disk."""
        registry = EngineRegistry(store_dir=tmp_path)
        engine = registry.get_or_create(dataset_id=6)

        rng = np.random.RandomState(3)
        X = pd.DataFrame(rng.randn(60, 4), columns=[f"f{i}" for i in range(4)])
        y = pd.Series((np.arange(60) % 3).astype(str))
        engine.fit(X, y)
        registry.save(dataset_id=6)

        registry.delete(dataset_id=6)

        assert registry.get(dataset_id=6) is None
        assert not (tmp_path / "engine_6.joblib").exists()

    def test_reload_after_delete_creates_fresh_engine(self, tmp_path: Path):
        """After delete(), get_or_create() must return an unfitted engine."""
        registry = EngineRegistry(store_dir=tmp_path)
        engine = registry.get_or_create(dataset_id=7)

        rng = np.random.RandomState(4)
        X = pd.DataFrame(rng.randn(60, 4), columns=[f"f{i}" for i in range(4)])
        y = pd.Series((np.arange(60) % 3).astype(str))
        engine.fit(X, y)
        registry.save(dataset_id=7)
        registry.delete(dataset_id=7)

        fresh = registry.get_or_create(dataset_id=7)
        assert fresh._fitted is False


class TestLockPreventsRaceCondition:
    def test_lock_prevents_race_condition(self, tmp_registry: EngineRegistry):
        """
        Two threads competing for the same dataset lock must serialize.
        The second thread must wait until the first releases before
        the critical section executes.

        Strategy: thread 1 acquires the lock, records start time, sleeps,
        then releases. Thread 2 tries to acquire; we verify it starts its
        critical section AFTER thread 1 releases.
        """
        DATASET_ID = 8
        timeline = []

        def thread_fn(label: str, hold_seconds: float = 0.0):
            lock = tmp_registry.lock(DATASET_ID)
            with lock:
                timeline.append((label, "acquired", time.monotonic()))
                time.sleep(hold_seconds)
                timeline.append((label, "released", time.monotonic()))

        t1 = threading.Thread(target=thread_fn, args=("T1", 0.05))
        t2 = threading.Thread(target=thread_fn, args=("T2", 0.0))

        t1.start()
        time.sleep(0.01)   # ensure T1 acquires first
        t2.start()

        t1.join(timeout=2)
        t2.join(timeout=2)

        assert len(timeline) == 4, f"Expected 4 events, got: {timeline}"

        # Extract events
        events = {(label, ev): ts for label, ev, ts in timeline}

        # T2 must not acquire until after T1 releases
        assert events[("T2", "acquired")] >= events[("T1", "released")], (
            "T2 acquired the lock before T1 released it — race condition!"
        )

    def test_lock_returns_same_object_for_same_dataset(
        self, tmp_registry: EngineRegistry
    ):
        """lock() called twice with the same dataset_id must return the same Lock."""
        lock1 = tmp_registry.lock(dataset_id=9)
        lock2 = tmp_registry.lock(dataset_id=9)

        assert lock1 is lock2

    def test_lock_returns_different_objects_for_different_datasets(
        self, tmp_registry: EngineRegistry
    ):
        """Different dataset_ids must have independent locks."""
        lock_a = tmp_registry.lock(dataset_id=10)
        lock_b = tmp_registry.lock(dataset_id=11)

        assert lock_a is not lock_b

    def test_singleton_get_engine_registry_returns_same_instance(self):
        """get_engine_registry() must always return the same singleton."""
        r1 = get_engine_registry()
        r2 = get_engine_registry()

        assert r1 is r2

    def test_status_reflects_engine_state(self, tmp_registry: EngineRegistry):
        """status() dict must accurately reflect exists/fitted/on_disk fields."""
        # Before any engine
        s = tmp_registry.status(dataset_id=12)
        assert s["exists"] is False
        assert s["fitted"] is False
        assert s["on_disk"] is False

        # After creating (but not fitting)
        tmp_registry.get_or_create(dataset_id=12)
        s = tmp_registry.status(dataset_id=12)
        assert s["exists"] is True
        assert s["fitted"] is False