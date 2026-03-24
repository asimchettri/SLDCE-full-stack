"""
Test: uncertain feedback flows end-to-end through the engine.
Verifies DECISION_MAP routing and meta-model handling.

Run:
    cd backend
    pytest tests/test_uncertain_feedback.py -v
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from services.ml_integration import apply_feedback, DECISION_MAP


# ── Unit test: DECISION_MAP routes uncertain correctly ──────────────────────

def test_decision_map_has_uncertain():
    assert "uncertain" in DECISION_MAP
    assert DECISION_MAP["uncertain"] == "uncertain"


def test_decision_map_all_keys():
    """All expected keys are present and map to valid engine values."""
    valid_engine_values = {"approve", "reject", "modify", "uncertain"}
    for key, value in DECISION_MAP.items():
        assert value in valid_engine_values, \
            f"DECISION_MAP['{key}'] = '{value}' is not a valid engine value"


# ── Unit test: apply_feedback translates uncertain correctly ─────────────────

def test_apply_feedback_translates_uncertain():
    """
    apply_feedback should translate 'uncertain' → engine.apply_feedback('uncertain').
    """
    mock_db = MagicMock()
    mock_engine = MagicMock()
    mock_engine.apply_feedback.return_value = {
        "sample_id": 1,
        "decision_type": "uncertain",
        "previous_label": 0,
        "updated_label": 0,
    }

    mock_registry = MagicMock()
    mock_registry.is_fitted.return_value = True
    mock_registry.get.return_value = mock_engine
    mock_registry.lock.return_value.__enter__ = MagicMock(return_value=None)
    mock_registry.lock.return_value.__exit__ = MagicMock(return_value=False)

    with patch("services.ml_integration.get_engine_registry", return_value=mock_registry):
        result = apply_feedback(
            db=mock_db,
            dataset_id=1,
            sample_id=42,
            previous_label=0,
            updated_label=0,
            decision_type="uncertain",
        )

    # Verify the engine received 'uncertain' not 'accept' or anything else
    mock_engine.apply_feedback.assert_called_once_with(
        sample_id=42,
        previous_label=0,
        updated_label=0,
        decision_type="uncertain",
        reviewer_comment="",
        reviewer_confidence=1.0,
    )
    assert result["decision_type"] == "uncertain"


def test_apply_feedback_rejects_invalid_decision():
    """Invalid decision_type should raise HTTPException."""
    from fastapi import HTTPException
    mock_db = MagicMock()

    mock_registry = MagicMock()
    mock_registry.is_fitted.return_value = True

    with patch("services.ml_integration.get_engine_registry", return_value=mock_registry):
        with pytest.raises(HTTPException) as exc_info:
            apply_feedback(
                db=mock_db,
                dataset_id=1,
                sample_id=1,
                previous_label=0,
                updated_label=1,
                decision_type="banana",  # invalid
            )
    assert exc_info.value.status_code == 400


# ── Integration test: meta-model stores uncertain feedback ───────────────────
def test_meta_model_handles_uncertain():
    """
    Uncertain feedback should be stored in engine feedback history.
    The meta-model should not crash when uncertain samples are present.
    """
    try:
        from self_learning_engine import SelfLearningCorrectionEngine
    except ImportError:
        pytest.skip("Engine not importable in this context")

    engine = SelfLearningCorrectionEngine()

    # Fit on toy data
    X = pd.DataFrame(np.random.randn(50, 4), columns=["f0", "f1", "f2", "f3"])
    y = pd.Series([0] * 25 + [1] * 25)
    engine.fit(X, y)

    # detect_noise() must be called before apply_feedback()
    detection_result = engine.detect_noise(X, y)

    # Pick any flagged sample — or use index 0 if none flagged
    flagged = detection_result.get("flagged_samples", [])
    sample_id = flagged[0]["sample_id"] if flagged else X.index[0]

    # Apply uncertain feedback
    record = engine.apply_feedback(
        sample_id=sample_id,
        previous_label=0,
        updated_label=0,
        decision_type="uncertain",
        reviewer_comment="not sure",
        reviewer_confidence=0.5,
    )

    assert record is not None
    assert record.get("decision_type") == "uncertain"

    # Meta-model update should not crash with uncertain feedback present
    result = engine.update_meta_model()
    assert isinstance(result, dict)
    assert "trained" in result