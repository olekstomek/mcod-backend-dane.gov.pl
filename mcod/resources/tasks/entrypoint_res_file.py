import json
import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict

from celery.result import EagerResult
from celery.states import SUCCESS
from django.apps import apps
from sentry_sdk import set_tag

from mcod.core.tasks import extended_shared_task
from mcod.resources.tasks.common import (
    prepare_url_task_result_for_resource,
    update_resource_openness_score,
    update_resource_verification_date,
)
from mcod.resources.tasks.entrypoint_common import report_exceptions
from mcod.resources.tasks.process_resource_file import process_resource_res_file_task

if TYPE_CHECKING:
    from mcod.resources.models import Resource, ResourceFile

logger = logging.getLogger("mcod")


def _run_file_validation(resource_file: "ResourceFile", update_file_archive: bool, update_link: bool) -> bool:
    logger.info("Resource file %s: running file validation task", resource_file.pk)
    eager_result_res_file: EagerResult = process_resource_res_file_task.apply(
        args=(resource_file.pk,),
        kwargs={"update_file_archive": update_file_archive, "update_link": update_link},
    )
    succeeded = eager_result_res_file.status == SUCCESS
    logger.info("Resource file %s: file validation task status=%s", resource_file.pk, succeeded)
    return succeeded


def _run_file_data_validation(resource: "Resource") -> None:
    logger.info("Resource %s: running file data validation task", resource.pk)
    Resource = apps.get_model("resources", "Resource")
    # Re-fetch full model instance instead of refresh_from_db(): Resource keeps
    # custom _cached_file relation cache, and stale main-file metadata can make
    # is_data_processable false right after file validation updated ResourceFile.
    resource = Resource.raw.get(pk=resource.pk)
    resource.revalidate_tabular_data(apply_on_commit=False)
    # Note: this _may_ also schedule increase_openness_score_task
    logger.info("Resource %s: file data validation task finished", resource.pk)


def _create_success_link_task_result(resource: "Resource") -> None:
    Resource = apps.get_model("resources", "Resource")
    TaskResult = apps.get_model("resources", "TaskResult")
    resource_for_link = Resource.raw.get(pk=resource.pk)
    result: Dict[str, Any] = prepare_url_task_result_for_resource(resource_for_link)
    url_task_result = TaskResult.objects.create(
        task_id=str(uuid.uuid4()),
        status=SUCCESS,
        result=json.dumps(result),
    )
    resource_for_link.link_tasks.add(url_task_result)
    Resource.raw.filter(pk=resource.pk).update(link_tasks_last_status=url_task_result.status)


def _schedule_es_and_rdf_update(resource: "Resource") -> None:
    logger.info("Resource %s: scheduling ES/RDF update", resource.pk)
    resource.refresh_from_db()
    resource.update_es_and_rdf_db()
    logger.info("Resource %s: ES/RDF update scheduling finished", resource.pk)


@extended_shared_task(
    ignore_result=True,
    # TODO(OTD-1446): Tasks' names aren't necessarily the same as import paths - check with Celery logs
    name="mcod.resources.tasks.entrypoint_process_resource_file_validation_task",
)
def entrypoint_process_resource_file_validation_task(
    resource_file_pk: int,
    update_verification_date: bool = True,
    update_file_archive: bool = False,
    update_link: bool = True,
):
    logger.info(
        "entrypoint_process_resource_file_validation_task started: resource_file_pk=%s "
        "update_verification_date=%s update_file_archive=%s update_link=%s",
        resource_file_pk,
        update_verification_date,
        update_file_archive,
        update_link,
    )
    ResourceFile = apps.get_model("resources", "ResourceFile")
    Resource = apps.get_model("resources", "Resource")
    resource_file: "ResourceFile" = ResourceFile.objects.get(pk=resource_file_pk)
    resource: "Resource" = Resource.objects.get(pk=resource_file.resource_id)
    resource_id = resource.pk
    set_tag("resource_id", str(resource_id))
    deferred_exceptions = []

    # 1. Run file validation task
    file_validation_succeeded = False
    with report_exceptions("Exception occurred during file validation task", suppress=True):
        file_validation_succeeded = _run_file_validation(resource_file, update_file_archive, update_link)
    if not file_validation_succeeded:
        logger.error(f"Failed to process resource file: pk = {resource_file_pk}")

    # 2. Run file data validation task
    if file_validation_succeeded and not deferred_exceptions:
        with report_exceptions(
            "Exception occurred during file data validation task",
            suppress=True,
        ) as errors:
            _run_file_data_validation(resource)
        deferred_exceptions.extend(errors)

    # 3. Create url validation task with SUCCESS status for resource
    if update_link and file_validation_succeeded and not deferred_exceptions:
        logger.info("Resource file %s: creating url-task-result with SUCCESS status", resource_file_pk)
        with report_exceptions(
            "Exception occurred during url-task-result creation",
            suppress=True,
        ) as errors:
            _create_success_link_task_result(resource)
        deferred_exceptions.extend(errors)

    # 4. Update openness and verification values in DB *before* scheduling ES/RDF update,
    # so that the ES worker reads the already-correct openness_score from the DB.
    with report_exceptions("Exception occurred during openness score update"):
        update_resource_openness_score(resource_id)

    if update_verification_date:
        with report_exceptions("Exception occurred during verification date update"):
            update_resource_verification_date(resource_id)

    # 5. Schedule ES/RDF update (only when the whole pipeline succeeded).
    if file_validation_succeeded and not deferred_exceptions:
        with report_exceptions(
            "Exception occurred during ES/RDF update scheduling",
            suppress=True,
        ) as errors:
            _schedule_es_and_rdf_update(resource)
        deferred_exceptions.extend(errors)

    if deferred_exceptions:
        deferred_exc = deferred_exceptions[0]
        logger.error(f"Exception occurred during process_resource_file_validation_task: {deferred_exc}")
        raise deferred_exc

    logger.info("entrypoint_process_resource_file_validation_task finished: resource_file_pk=%s", resource_file_pk)
