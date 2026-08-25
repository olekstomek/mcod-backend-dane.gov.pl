import datetime
import logging
from typing import Optional

import sentry_sdk
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.db.models import Model

from .models import Category, Subject, SubmissionEvent

logger = logging.getLogger("mcod")


def create_submission_event(
    *,
    submission_date: datetime.datetime,
    subject: Subject,
    category: Optional[Category] = None,
    reference_object: Optional[Model] = None,
) -> Optional[SubmissionEvent]:
    """Create and persist a submission event, returning None when validation or save fails."""
    try:
        event = SubmissionEvent(
            subject=subject.value,
            category=category.value if category is not None else "",
            submission_date=submission_date,
        )
        if reference_object is not None:
            event.reference_object = reference_object
        event.full_clean()
        event.save()
    except (ValidationError, DatabaseError) as e:
        logger.error(f"Failed to create submission event: {e}")
        sentry_sdk.capture_exception(e)
        # Return None to allow graceful failure without interrupting the caller
        return None

    return event
