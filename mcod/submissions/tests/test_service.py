import datetime
from typing import Optional
from unittest.mock import patch

import pytest

from mcod.submissions.models import Category, Subject, SubmissionEvent
from mcod.submissions.service import create_submission_event
from mcod.suggestions.factories import DatasetSubmissionFactory

_SUBMISSION_DATE = datetime.datetime(2026, 1, 1, 12, 0, 0)

_VALID_SUBJECT_CATEGORY_COMBINATIONS = [
    # Subject.DATA — generic combinations (not tied to a specific model)
    pytest.param(Subject.DATA, Category.SHARING, id="data_with_sharing"),
    pytest.param(Subject.DATA, Category.STANDARDS, id="data_with_standards"),
    pytest.param(Subject.DATA, Category.HVD, id="data_with_hvd"),
    pytest.param(Subject.DATA, Category.DGA, id="data_with_dga"),
    pytest.param(Subject.DATA, Category.OTHER, id="data_with_other"),
    pytest.param(Subject.DATA, Category.SUGGEST_DATA, id="data_with_suggest_data"),
    pytest.param(Subject.DATA, Category.FEEDBACK, id="data_with_feedback"),
    pytest.param(Subject.DATA, Category.SUGGEST_REUSE, id="data_with_suggest_reuse"),
    # Subject.PORTAL dependencies
    pytest.param(Subject.PORTAL, Category.FEATURES, id="portal_with_features"),
    pytest.param(Subject.PORTAL, Category.PROFILES, id="portal_with_profiles"),
    pytest.param(Subject.PORTAL, Category.PERMISSIONS, id="portal_with_permissions"),
    pytest.param(Subject.PORTAL, Category.BUGS, id="portal_with_bugs"),
    pytest.param(Subject.PORTAL, Category.OTHER, id="portal_with_other"),
    # Subjects without categories
    pytest.param(Subject.DATA_PROTECTION, None, id="data_protection_without_category"),
    pytest.param(Subject.LEGAL, None, id="legal_without_category"),
    pytest.param(Subject.OTHER, None, id="other_without_category"),
]


@pytest.mark.parametrize("subject, category", _VALID_SUBJECT_CATEGORY_COMBINATIONS)
def test_create_submission_event(subject: Subject, category: Optional[Category]) -> None:
    # GIVEN
    assert SubmissionEvent.objects.count() == 0

    # WHEN
    submission_event: Optional[SubmissionEvent] = create_submission_event(
        subject=subject,
        category=category,
        submission_date=_SUBMISSION_DATE,
    )

    # THEN
    assert SubmissionEvent.objects.count() == 1
    assert submission_event is not None
    assert submission_event.subject == subject
    if category is None:
        assert submission_event.category == ""
    else:
        assert submission_event.category == category
    assert submission_event.submission_date == _SUBMISSION_DATE


def test_create_submission_event_with_reference_object() -> None:
    # GIVEN
    assert SubmissionEvent.objects.count() == 0
    with patch("mcod.suggestions.models.create_submission_event"):
        reference_submission = DatasetSubmissionFactory.create()

    # WHEN
    submission_event: Optional[SubmissionEvent] = create_submission_event(
        reference_object=reference_submission,
        submission_date=reference_submission.created,
        subject=Subject.DATA,
        category=Category.SUGGEST_DATA,
    )

    # THEN
    assert SubmissionEvent.objects.count() == 1
    assert submission_event is not None
    assert submission_event.subject == Subject.DATA
    assert submission_event.category == Category.SUGGEST_DATA
    assert submission_event.submission_date == reference_submission.created
    assert submission_event.reference_object_id == reference_submission.id
    assert submission_event.reference_object == reference_submission


_INVALID_SUBJECT_CATEGORY_COMBINATIONS = [
    pytest.param(Subject.DATA, Category.FEATURES, id="data_with_portal_only_category"),
    pytest.param(Subject.PORTAL, Category.SHARING, id="portal_with_data_only_category"),
    pytest.param(Subject.DATA_PROTECTION, Category.SHARING, id="data_protection_with_any_category"),
    pytest.param(Subject.LEGAL, Category.HVD, id="legal_with_any_category"),
    pytest.param(Subject.OTHER, Category.BUGS, id="other_with_any_category"),
    pytest.param(Subject.DATA, None, id="data_missing_required_category"),
    pytest.param(Subject.PORTAL, None, id="portal_missing_required_category"),
]


@pytest.mark.parametrize("subject, category", _INVALID_SUBJECT_CATEGORY_COMBINATIONS)
def test_create_submission_event_with_invalid_subject_category(subject: Subject, category: Optional[Category]) -> None:
    # GIVEN
    assert SubmissionEvent.objects.count() == 0

    # WHEN
    with patch("mcod.submissions.service.sentry_sdk.capture_exception") as mock_capture:
        submission_event: Optional[SubmissionEvent] = create_submission_event(
            subject=subject,
            category=category,
            submission_date=_SUBMISSION_DATE,
        )

    # THEN
    assert SubmissionEvent.objects.count() == 0
    assert submission_event is None
    mock_capture.assert_called_once()
