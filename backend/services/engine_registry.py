"""
engine_registry.py
------------------
Manages one SelfLearningCorrectionEngine instance per dataset.

Responsibilities:
  - Create a new engine for a dataset if one does not exist
  - Persist engines to disk via joblib (backend/engine_store/)
  - Load engines from disk on cache miss or server restart
  - Provide a single access point for all services

Thread safety:
  The engine itself is not thread-safe (per Dev 1's README).
  A per-dataset lock is used to prevent concurrent fit/detect/feedback
  calls on the same engine instance.

Usage:
    from services.engine_registry import get_engine_registry
    registry = get_engine_registry()
    engine = registry.get_or_create(dataset_id)
    registry.save(dataset_id)
"""

import threading
import logging
from pathlib import Path
from typing import Dict, Optional

import joblib

from self_learning_engine import SelfLearningCorrectionEngine

logger = logging.getLogger(__name__)

# Path to engine store directory — relative to this file's location
ENGINE_STORE_DIR = Path(__file__).parent.parent / "engine_store"


class EngineRegistry:
    """
    Thread-safe registry of SelfLearningCorrectionEngine instances.

    One engine per dataset_id. Engines are persisted to disk with
    joblib so state survives server restarts.

    Attributes
    ----------
    _engines : Dict[int, SelfLearningCorrectionEngine]
        In-memory cache of loaded engines.
    _locks : Dict[int, threading.Lock]
        Per-dataset locks to prevent concurrent mutation.
    _registry_lock : threading.Lock
        Protects the _locks dict itself during creation.
    """

    def __init__(self, store_dir: Path = ENGINE_STORE_DIR) -> None:
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self._engines: Dict[int, SelfLearningCorrectionEngine] = {}
        self._locks: Dict[int, threading.Lock] = {}
        self._registry_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_or_create(self, dataset_id: int) -> SelfLearningCorrectionEngine:
        """
        Return the engine for dataset_id.

        Load order:
          1. In-memory cache
          2. Disk (joblib file)
          3. Fresh engine

        Parameters
        ----------
        dataset_id : int

        Returns
        -------
        SelfLearningCorrectionEngine
        """
        if dataset_id in self._engines:
            return self._engines[dataset_id]

        engine = self._load(dataset_id)
        if engine is not None:
            self._engines[dataset_id] = engine
            logger.info(f"Engine for dataset {dataset_id} loaded from disk")
            return engine

        engine = SelfLearningCorrectionEngine()
        self._engines[dataset_id] = engine
        logger.info(f"Fresh engine created for dataset {dataset_id}")
        return engine

    def get(self, dataset_id: int) -> Optional[SelfLearningCorrectionEngine]:
        """
        Return engine only if it already exists in memory or on disk.
        Returns None if no engine has been created for this dataset yet.

        Use this in services that should NOT create a new engine —
        e.g. detect_noise requires fit() to have been called first.

        Parameters
        ----------
        dataset_id : int

        Returns
        -------
        Optional[SelfLearningCorrectionEngine]
        """
        if dataset_id in self._engines:
            return self._engines[dataset_id]

        engine = self._load(dataset_id)
        if engine is not None:
            self._engines[dataset_id] = engine
            return engine

        return None

    def save(self, dataset_id: int) -> bool:
        """
        Persist the engine for dataset_id to disk.

        Call this after any operation that mutates engine state:
        fit(), apply_feedback(), retrain_if_ready().

        Parameters
        ----------
        dataset_id : int

        Returns
        -------
        bool
            True if saved, False if engine not found in memory.
        """
        engine = self._engines.get(dataset_id)
        if engine is None:
            logger.warning(
                f"Cannot save: no engine in memory for dataset {dataset_id}"
            )
            return False

        path = self._engine_path(dataset_id)
        try:
            joblib.dump(engine, path)
            logger.info(f"Engine for dataset {dataset_id} saved → {path}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to save engine for dataset {dataset_id}: {e}"
            )
            return False

    def delete(self, dataset_id: int) -> bool:
        """
        Remove engine from memory and delete its file from disk.

        Call this when a dataset is deleted.

        Parameters
        ----------
        dataset_id : int

        Returns
        -------
        bool
            True if file existed and was deleted.
        """
        self._engines.pop(dataset_id, None)
        self._locks.pop(dataset_id, None)

        path = self._engine_path(dataset_id)
        if path.exists():
            path.unlink()
            logger.info(f"Engine file deleted for dataset {dataset_id}")
            return True
        return False

    def is_fitted(self, dataset_id: int) -> bool:
        """
        Return True if an engine exists and has been fitted for this dataset.

        Parameters
        ----------
        dataset_id : int
        """
        engine = self.get(dataset_id)
        if engine is None:
            return False
        return engine._fitted

    def lock(self, dataset_id: int) -> threading.Lock:
        """
        Return the per-dataset threading lock.

        Always use this as a context manager around any engine mutation:

            with registry.lock(dataset_id):
                engine = registry.get_or_create(dataset_id)
                engine.fit(X, y)
                registry.save(dataset_id)

        Parameters
        ----------
        dataset_id : int

        Returns
        -------
        threading.Lock
        """
        with self._registry_lock:
            if dataset_id not in self._locks:
                self._locks[dataset_id] = threading.Lock()
            return self._locks[dataset_id]

    def status(self, dataset_id: int) -> Dict:
        """
        Return a status dict for a dataset's engine.
        Useful for health check and debug endpoints.

        Parameters
        ----------
        dataset_id : int

        Returns
        -------
        Dict with keys: exists, fitted, on_disk, file_path
        """
        engine = self.get(dataset_id)
        path = self._engine_path(dataset_id)

        return {
            "dataset_id": dataset_id,
            "exists": engine is not None,
            "fitted": engine._fitted if engine is not None else False,
            "on_disk": path.exists(),
            "file_path": str(path),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _engine_path(self, dataset_id: int) -> Path:
        return self.store_dir / f"engine_{dataset_id}.joblib"

    def _load(self, dataset_id: int) -> Optional[SelfLearningCorrectionEngine]:
        path = self._engine_path(dataset_id)
        if not path.exists():
            return None
        try:
            engine = joblib.load(path)
            return engine
        except Exception as e:
            logger.error(
                f"Failed to load engine for dataset {dataset_id} "
                f"from {path}: {e}"
            )
            return None


# ---------------------------------------------------------------------------
# Singleton — one registry for the entire FastAPI process
# ---------------------------------------------------------------------------

_registry_instance: Optional[EngineRegistry] = None


def get_engine_registry() -> EngineRegistry:
    """
    Return the singleton EngineRegistry instance.

    Import and call this in any service that needs engine access:

        from services.engine_registry import get_engine_registry

        registry = get_engine_registry()
        engine = registry.get_or_create(dataset_id)
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = EngineRegistry()
    return _registry_instance