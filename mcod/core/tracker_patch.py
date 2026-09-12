"""
Request-local optimization for django-model-utils FieldTracker.

During read-only serialization flows, skipping saved fields initialization
reduces model instantiation overhead while keeping tracker objects created.
"""

from contextvars import ContextVar

from model_utils.tracker import FieldInstanceTracker

_tracker_disabled = ContextVar("disable_modeltracker", default=False)

_original_set_saved_fields = FieldInstanceTracker.set_saved_fields


def _conditional_set_saved_fields(self, fields=None):
    if _tracker_disabled.get():
        return

    return _original_set_saved_fields(self, fields=fields)


FieldInstanceTracker.set_saved_fields = _conditional_set_saved_fields
