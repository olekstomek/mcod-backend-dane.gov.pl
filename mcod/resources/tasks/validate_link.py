import logging

from celery.signals import task_failure, task_postrun, task_prerun
from django.apps import apps
from sentry_sdk import set_tag

from mcod.core.tasks import extended_shared_task
from mcod.resources.tasks.common import save_task_result_for_resource_after_task_failure

logger = logging.getLogger("mcod")


@extended_shared_task(
    ignore_result=False,
    # TODO(OTD-1446): Tasks' names aren't necessarily the same as import paths - check with Celery logs
    name="mcod.resources.tasks.validate_link",
)
def validate_link(resource_id: int, /):
    set_tag("resource_id", str(resource_id))
    Resource = apps.get_model("resources", "Resource")
    resource = Resource.raw.get(id=resource_id)
    logger.debug(f"Validating link of resource with id {resource_id}")
    resource.check_link_status()
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


@task_postrun.connect(sender=validate_link)
def validate_link_task_postrun_handler(sender, task_id, task, signal, **kwargs):
    resource_id = int(kwargs["args"][0])
    Resource = apps.get_model("resources", "Resource")
    TaskResult = apps.get_model("resources", "TaskResult")
    task_result = TaskResult.objects.get_task(task_id)
    Resource.raw.filter(pk=resource_id).update(
        link_tasks_last_status=task_result.status,
        verified=task_result.date_done,
    )


@task_failure.connect(sender=validate_link)
def validate_link_task_failure_handler(sender, task_id, exception, args, traceback, einfo, signal, **kwargs):
    """Role of this handler is to add the exception details to corresponding task result object."""
    resource_id = int(args[0])
    save_task_result_for_resource_after_task_failure(task_id, resource_id, exception)
