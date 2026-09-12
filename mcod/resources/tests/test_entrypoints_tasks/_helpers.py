from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from celery.app.task import Task as CeleryBaseTask
from celery.contrib.django.task import DjangoTask


def build_signature(task_calls, task_name: str, method_name: str, return_value=None):
    signature = MagicMock()

    def mark_call(*args, **kwargs):
        task_calls.append((task_name, method_name))
        return return_value

    getattr(signature, method_name).side_effect = mark_call
    return signature


def build_status_signature(status: str):
    signature = MagicMock()
    signature.apply.return_value = MagicMock(status=status)
    return signature


@contextmanager
def assert_no_extra_celery_tasks():
    """
    Patches Celery base-class dispatch methods as a safety net.

    Any task dispatch NOT already intercepted by a more-specific instance-level
    patch will be recorded and reported as an AssertionError on exit.

    Instance-level patches (e.g. ``patch("module.some_task.apply", ...)``) take
    precedence over these class-level guards via Python's normal MRO, so
    intentionally tracked tasks are completely unaffected.
    """
    unexpected = []

    def _guard(method_name):
        def _fn(self, *args, **kwargs):
            unexpected.append((self.name.rsplit(".", 1)[-1], method_name))
            return MagicMock()

        return _fn

    with patch.object(CeleryBaseTask, "apply", _guard("apply")), patch.object(
        CeleryBaseTask, "apply_async", _guard("apply_async")
    ), patch.object(DjangoTask, "apply_async_on_commit", _guard("apply_async_on_commit")):
        yield

    assert unexpected == [], f"Unexpected Celery task dispatches: {unexpected}"
