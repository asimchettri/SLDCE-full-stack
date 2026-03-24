"""
test_feedback_service.py
------------------------
Unit tests for services/feedback_service.py

Tests:
  - test_get_stats_counts_approve_not_accept
  - test_get_patterns_returns_acceptance_by_confidence
  - test_create_feedback_from_suggestion
  - additional coverage for get_feedback, count_feedback, get_feedback_by_id
"""

import json
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.dataset import Sample, Detection, Suggestion, Feedback
from services.feedback_service import FeedbackService

DATASET_ID = 42


# ── DB fixture helpers ────────────────────────────────────────────────────────

def _insert_sample(db: Session, dataset_id: int = DATASET_ID,
                   idx: int = 0, label: int = 0) -> Sample:
    s = Sample(
        dataset_id=dataset_id,
        sample_index=idx,
        features=json.dumps([1.0, 2.0, 3.0, 4.0]),
        original_label=label,
        current_label=label,
        is_suspicious=True,
        is_corrected=False,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _insert_detection(db: Session, sample: Sample,
                      confidence: float = 0.8,
                      anomaly: float = 0.7,
                      priority: float = 0.75,
                      predicted_label: int = 1,
                      iteration: int = 1) -> Detection:
    d = Detection(
        sample_id=sample.id,
        iteration=iteration,
        confidence_score=confidence,
        anomaly_score=anomaly,
        predicted_label=predicted_label,
        priority_score=priority,
        rank=1,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def _insert_suggestion(db: Session, detection: Detection,
                       suggested_label: int = 1,
                       confidence: float = 0.85,
                       status: str = "pending") -> Suggestion:
    sg = Suggestion(
        detection_id=detection.id,
        suggested_label=suggested_label,
        confidence=confidence,
        reason="Test suggestion",
        status=status,
    )
    db.add(sg)
    db.commit()
    db.refresh(sg)
    return sg


def _insert_feedback(db: Session, suggestion: Suggestion,
                     sample: Sample,
                     action: str = "approve",
                     final_label: int = 1,
                     iteration: int = 1) -> Feedback:
    f = Feedback(
        suggestion_id=suggestion.id,
        sample_id=sample.id,
        action=action,
        final_label=final_label,
        iteration=iteration,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _full_chain(db: Session, dataset_id: int = DATASET_ID,
                action: str = "approve", idx: int = 0,
                confidence: float = 0.8, priority: float = 0.75):
    """Insert sample → detection → suggestion → feedback in one call."""
    sample = _insert_sample(db, dataset_id=dataset_id, idx=idx)
    detection = _insert_detection(db, sample, confidence=confidence,
                                  priority=priority)
    suggestion = _insert_suggestion(db, detection)
    feedback = _insert_feedback(db, suggestion, sample, action=action)
    return sample, detection, suggestion, feedback


# ── create_feedback_from_suggestion ──────────────────────────────────────────

class TestCreateFeedbackFromSuggestion:
    def test_create_feedback_from_suggestion(self, db: Session):
        """
        create_feedback_from_suggestion() must create a Feedback row
        linked to the correct sample_id and with the given action/label.
        """
        sample = _insert_sample(db, idx=0)
        detection = _insert_detection(db, sample)
        suggestion = _insert_suggestion(db, detection)

        feedback = FeedbackService.create_feedback_from_suggestion(
            db=db,
            suggestion=suggestion,
            action="approve",
            final_label=1,
        )

        assert feedback.id is not None
        assert feedback.suggestion_id == suggestion.id
        assert feedback.sample_id == sample.id
        assert feedback.action == "approve"
        assert feedback.final_label == 1
        assert feedback.iteration == detection.iteration

    def test_create_feedback_updates_existing(self, db: Session):
        """
        Calling create_feedback_from_suggestion() twice on the same suggestion
        must UPDATE the existing record, not create a duplicate.
        """
        sample = _insert_sample(db, idx=1)
        detection = _insert_detection(db, sample)
        suggestion = _insert_suggestion(db, detection)

        FeedbackService.create_feedback_from_suggestion(
            db, suggestion, action="approve", final_label=1
        )
        updated = FeedbackService.create_feedback_from_suggestion(
            db, suggestion, action="reject", final_label=0
        )

        count = db.query(Feedback).filter(
            Feedback.suggestion_id == suggestion.id
        ).count()
        assert count == 1
        assert updated.action == "reject"

    def test_create_feedback_raises_404_for_missing_detection(self, db: Session):
        """
        create_feedback_from_suggestion() must raise HTTP 404 when the
        detection referenced by the suggestion does not exist.
        """
        sg = Suggestion(
            detection_id=99999,
            suggested_label=1,
            confidence=0.9,
            reason="Orphan",
            status="pending",
        )
        db.add(sg)
        db.commit()
        db.refresh(sg)

        with pytest.raises(HTTPException) as exc_info:
            FeedbackService.create_feedback_from_suggestion(
                db, sg, action="approve", final_label=1
            )

        assert exc_info.value.status_code == 404


# ── get_stats ─────────────────────────────────────────────────────────────────

class TestGetStats:
    def test_get_stats_counts_approve_not_accept(self, db: Session):
        """
        get_stats() must count action == 'approve' under 'accepted'.
        The engine uses 'approve', not 'accept'. This test locks that in.
        """
        _full_chain(db, action="approve", idx=0)
        _full_chain(db, action="approve", idx=1)
        _full_chain(db, action="reject",  idx=2)
        _full_chain(db, action="modify",  idx=3)

        stats = FeedbackService.get_stats(db, DATASET_ID)

        assert stats["accepted"] == 2
        assert stats["rejected"] == 1
        assert stats["modified"] == 1
        assert stats["total_feedback"] == 4

    def test_get_stats_acceptance_rate_calculation(self, db: Session):
        """acceptance_rate = (accepted + modified) / total * 100 → 80%"""
        _full_chain(db, action="approve", idx=0)
        _full_chain(db, action="approve", idx=1)
        _full_chain(db, action="approve", idx=2)
        _full_chain(db, action="modify",  idx=3)
        _full_chain(db, action="reject",  idx=4)

        stats = FeedbackService.get_stats(db, DATASET_ID)

        assert stats["acceptance_rate"] == 80.0

    def test_get_stats_returns_zeros_for_empty_dataset(self, db: Session):
        """get_stats() on a dataset with no feedback must return all zeros."""
        stats = FeedbackService.get_stats(db, dataset_id=9999)

        assert stats["total_feedback"] == 0
        assert stats["accepted"] == 0
        assert stats["acceptance_rate"] == 0.0

    def test_get_stats_does_not_count_accept_string(self, db: Session):
        """
        Legacy 'accept' action must NOT be counted under 'accepted'.
        Only 'approve' counts.
        """
        sample = _insert_sample(db, idx=10)
        detection = _insert_detection(db, sample)
        suggestion = _insert_suggestion(db, detection)
        _insert_feedback(db, suggestion, sample, action="accept")

        stats = FeedbackService.get_stats(db, DATASET_ID)

        assert stats["accepted"] == 0


# ── get_patterns ──────────────────────────────────────────────────────────────

class TestGetPatterns:
    def test_get_patterns_returns_acceptance_by_confidence(self, db: Session):
        """
        get_patterns() must return a dict with 'acceptance_by_confidence'
        grouping detections by confidence range.
        """
        _full_chain(db, action="approve", idx=0, confidence=0.85)
        _full_chain(db, action="reject",  idx=1, confidence=0.45)

        result = FeedbackService.get_patterns(db, DATASET_ID)

        assert "acceptance_by_confidence" in result
        assert result["patterns_found"] == 2
        for range_data in result["acceptance_by_confidence"].values():
            assert "total" in range_data
            assert "accepted" in range_data
            assert "acceptance_rate" in range_data

    def test_get_patterns_returns_acceptance_by_priority(self, db: Session):
        """get_patterns() must also return acceptance_by_priority breakdown."""
        _full_chain(db, action="approve", idx=0, priority=0.8)
        _full_chain(db, action="reject",  idx=1, priority=0.2)

        result = FeedbackService.get_patterns(db, DATASET_ID)

        assert "acceptance_by_priority" in result
        assert isinstance(result["acceptance_by_priority"], dict)

    def test_get_patterns_empty_returns_message(self, db: Session):
        """get_patterns() with no feedback must return patterns_found=0."""
        result = FeedbackService.get_patterns(db, dataset_id=9999)

        assert result["patterns_found"] == 0
        assert "message" in result

    def test_get_patterns_acceptance_rate_in_range(self, db: Session):
        """All acceptance_rate values must be 0–100."""
        for i in range(6):
            action = "approve" if i % 2 == 0 else "reject"
            _full_chain(db, action=action, idx=i, confidence=0.5 + i * 0.05)

        result = FeedbackService.get_patterns(db, DATASET_ID)

        for range_data in result["acceptance_by_confidence"].values():
            assert 0.0 <= range_data["acceptance_rate"] <= 100.0

    def test_get_patterns_with_iteration_filter(self, db: Session):
        """get_patterns() with iteration filter returns only that iteration."""
        sample0 = _insert_sample(db, idx=20)
        det0 = _insert_detection(db, sample0, iteration=1)
        sug0 = _insert_suggestion(db, det0)
        _insert_feedback(db, sug0, sample0, action="approve", iteration=1)

        sample1 = _insert_sample(db, idx=21)
        det1 = _insert_detection(db, sample1, iteration=2)
        sug1 = _insert_suggestion(db, det1)
        _insert_feedback(db, sug1, sample1, action="reject", iteration=2)

        result = FeedbackService.get_patterns(db, DATASET_ID, iteration=1)

        assert result["patterns_found"] == 1


# ── get_feedback / count_feedback ─────────────────────────────────────────────

class TestGetFeedback:
    def test_get_feedback_returns_list(self, db: Session):
        """get_feedback() must return a list of Feedback objects."""
        _full_chain(db, action="approve", idx=0)
        _full_chain(db, action="reject",  idx=1)

        result = FeedbackService.get_feedback(db, dataset_id=DATASET_ID)

        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_feedback_action_filter(self, db: Session):
        """get_feedback() with action filter returns only matching rows."""
        _full_chain(db, action="approve", idx=0)
        _full_chain(db, action="reject",  idx=1)
        _full_chain(db, action="approve", idx=2)

        result = FeedbackService.get_feedback(
            db, dataset_id=DATASET_ID, action="approve"
        )

        assert all(f.action == "approve" for f in result)
        assert len(result) == 2

    def test_get_feedback_by_id_raises_404_for_missing(self, db: Session):
        """get_feedback_by_id() must raise HTTP 404 for unknown ID."""
        with pytest.raises(HTTPException) as exc_info:
            FeedbackService.get_feedback_by_id(db, feedback_id=99999)

        assert exc_info.value.status_code == 404

    def test_count_feedback_returns_correct_count(self, db: Session):
        """count_feedback() must return the exact number of rows."""
        _full_chain(db, action="approve", idx=0)
        _full_chain(db, action="approve", idx=1)
        _full_chain(db, action="reject",  idx=2)

        count = FeedbackService.count_feedback(db, dataset_id=DATASET_ID)

        assert count == 3

    def test_count_feedback_with_action_filter(self, db: Session):
        """count_feedback() with action filter counts only matching rows."""
        _full_chain(db, action="approve", idx=0)
        _full_chain(db, action="reject",  idx=1)

        count = FeedbackService.count_feedback(
            db, dataset_id=DATASET_ID, action="reject"
        )

        assert count == 1