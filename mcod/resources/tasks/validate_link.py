import json
import logging
import uuid
from datetime import datetime
from typing import List

import sentry_sdk
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import task_prerun
from django.apps import apps
from django.conf import settings
from django.utils import timezone
from sentry_sdk import set_tag

from mcod.core.tasks import extended_shared_task
from mcod.lib.exceptions import (
    InvalidContentType,
    InvalidResponseCode,
    InvalidUrl,
    UnsupportedContentType,
)
from mcod.unleash import is_enabled

logger = logging.getLogger("mcod")


if is_enabled("S69_resource_link_validation_chunk"):  # noqa: C901

    def _validate_link(resource_id: int, task_id: str):
        set_tag("resource_id", str(resource_id))
        Resource = apps.get_model("resources", "Resource")
        resource = Resource.objects.get(id=resource_id)
        logger.debug("Validating link of resource with id %s", resource_id)
        TaskResult = apps.get_model("resources", "TaskResult")

        # get_task() is expected to return a proxy instance of TaskResult,
        # which provides custom helper methods (e.g. mark_task_failure).
        task_result: TaskResult = TaskResult.objects.get_task(task_id)

        if not task_result.pk:
            task_result.save()
        if not resource.link_tasks.filter(pk=task_result.pk).exists():
            resource.link_tasks.add(task_result)

        payload = {
            "uuid": str(resource.uuid),
            "link": resource.link,
            "format": resource.format,
            "type": resource.type,
        }

        known_exc = (InvalidUrl, UnsupportedContentType, InvalidContentType, InvalidResponseCode)
        try:
            resource.check_link_status()
            task_result.status = "SUCCESS"
        except Exception as exc:
            logger.exception("check_link_status failed")
            failure_payload = {
                "exc_type": type(exc).__name__,
                "exc_message": str(exc) if isinstance(exc, known_exc) else "Unknown error occurred",
            }
            task_result.result = json.dumps({**payload, **failure_payload})
            task_result.status = "FAILURE"
            task_result.content_type = "application/json"
            task_result.content_encoding = "utf-8"
            task_result.meta = '{"children": []}'
            raise
        finally:
            check_time: datetime = timezone.now()
            task_result.date_done = check_time
            task_result.save()
            Resource.raw.filter(pk=resource_id).update(
                link_tasks_last_status=task_result.status,
                verified=check_time,
            )
        return payload

    @extended_shared_task(
        ignore_result=True,
        bind=True,
        # TODO(OTD-1446): Tasks' names aren't necessarily the same as import paths - check with Celery logs
        name="mcod.resources.tasks.validate_link",
    )
    def validate_link(self, resource_id: int, /):
        return _validate_link(resource_id, self.request.id)

    @extended_shared_task(
        ignore_result=False,
        bind=True,
        name="mcod.resources.tasks.validate_links_batch",
        soft_time_limit=settings.CELERY_SOFT_TIME_LIMIT,
        time_limit=settings.CELERY_TIME_LIMIT,
    )
    def validate_links_batch(self, resource_ids: List[int], /):
        """
        Validate external links for a batch of resources.

        The task processes resource IDs sequentially and validates each link using
        the internal `_validate_link` helper.

        A soft time limit is used to prevent long-running batches from blocking
        a worker process indefinitely. When the soft limit is exceeded, the task
        stops processing further resources in a controlled manner and logs partial
        progress. A hard time limit acts as a safety net to forcibly terminate the
        task if needed.

        Validation results are persisted directly to the database; the Celery result
        backend is disabled for this task. Individual validation failures are logged
        and do not abort the batch.
        """
        ok = 0
        failed = 0
        total = len(resource_ids)
        try:

            logger.debug(f"Validating batch of {total} links")
            for resource_id in resource_ids:
                try:
                    # We create a new UUID for each individual link validation to maintain history
                    surrogate_task_id = str(uuid.uuid4())
                    _validate_link(resource_id, surrogate_task_id)
                    ok += 1
                except SoftTimeLimitExceeded:
                    # don't treat soft limit as a per-resource failure
                    raise
                except Exception as exc:
                    sentry_sdk.api.capture_exception(exc)
                    failed += 1
                    logger.exception(f"Error validating resource {resource_id} link in batch")
        except SoftTimeLimitExceeded as exc:
            logger.warning(f"Soft time limit exceeded in batch {self.request.id} (processed={ok + failed}/{total})")
            sentry_sdk.api.capture_exception(exc)
            return
        return

else:

    @extended_shared_task(
        ignore_result=False,
        bind=True,
        # TODO(OTD-1446): Tasks' names aren't necessarily the same as import paths - check with Celery logs
        name="mcod.resources.tasks.validate_link",
    )
    def validate_link(self, resource_id: int, /):
        set_tag("resource_id", str(resource_id))
        Resource = apps.get_model("resources", "Resource")
        resource = Resource.objects.get(id=resource_id)
        logger.debug(f"Validating link of resource with id {resource_id}")
        task_id = self.request.id
        TaskResult = apps.get_model("resources", "TaskResult")
        task_result = TaskResult.objects.get_task(task_id)
        try:
            resource.check_link_status()
        except Exception as exc:
            result = {
                "exc_type": exc.__class__.__name__,
                "exc_message": str(exc),
                "uuid": str(resource.uuid),
                "link": resource.link,
                "format": resource.format,
                "type": resource.type,
            }
            task_result.result = json.dumps(result)
            task_result.status = "FAILURE"
            task_result.content_type = "application/json"
            task_result.content_encoding = "utf-8"
            task_result.meta = '{"children": []}'
            self.ignore_result = True  # to prevent overwriting task result when task raise exception
            raise
        else:
            task_result.status = "SUCCESS"
        finally:
            check_time: datetime = timezone.now()
            task_result.date_done = check_time
            task_result.save()
            Resource.raw.filter(pk=resource_id).update(
                link_tasks_last_status=task_result.status,
                verified=check_time,
            )
        return {
            "uuid": str(resource.uuid),
            "link": resource.link,
            "format": resource.format,
            "type": resource.type,
        }


@task_prerun.connect(sender=validate_link)
def validate_link_task_prerun_handler(sender, task_id, task, signal, **kwargs):
    """
    Role of this handler is to add PENDING task to list of resource's link tasks.

    Note:
        - cannot be moved to the beginning of the sender task because of using atomic=True
    """
    try:
        resource_id = int(kwargs["args"][0])

        Resource = apps.get_model("resources", "Resource")
        TaskResult = apps.get_model("resources", "TaskResult")

        resource = Resource.objects.get(pk=resource_id)
        result_task = TaskResult.objects.get_task(task_id)
        result_task.save()  # need to call .save() because it is not in db yet
        resource.link_tasks.add(result_task)
        Resource.raw.filter(pk=resource_id).update(link_tasks_last_status=result_task.status)
    except Exception as exc:
        logger.exception(f"Exception occurred during link task prerun handler: {exc}")
