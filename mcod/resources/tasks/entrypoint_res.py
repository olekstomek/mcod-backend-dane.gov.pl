import logging
from typing import TYPE_CHECKING, Optional

from celery.result import EagerResult
from celery.states import SUCCESS
from django.apps import apps
from sentry_sdk import set_tag

from mcod.core.tasks import extended_shared_task
from mcod.resources.tasks.common import (
    update_resource_openness_score,
    update_resource_verification_date,
)
from mcod.resources.tasks.entrypoint_common import report_exceptions
from mcod.resources.tasks.process_resource_file import process_resource_res_file_task
from mcod.resources.tasks.process_resource_from_url import process_resource_from_url_task

if TYPE_CHECKING:
    from mcod.resources.models import Resource

logger = logging.getLogger("mcod")


def _run_url_validation(resource_pk: int, forced_file_changed: bool) -> bool:
    logger.info("Resource %s: running url validation task", resource_pk)
    eager_result_res_url: EagerResult = process_resource_from_url_task.apply(
        args=(resource_pk,),
        kwargs={"forced_file_changed": forced_file_changed},
    )
    succeeded = eager_result_res_url.status == SUCCESS
    logger.info("Resource %s: url validation task status=%s", resource_pk, succeeded)
    return succeeded


def _run_file_validation(resource: "Resource", update_file_archive: bool) -> bool:
    logger.info("Resource %s: running file validation task", resource.pk)
    main_file_qs = resource.files.filter(is_main=True)
    if not main_file_qs.exists():
        logger.info(f"Resource {resource.pk} has no main file")
        logger.info("Resource %s: file validation task status=True", resource.pk)
        return True

    main_file = main_file_qs.first()
    eager_result_res_file: EagerResult = process_resource_res_file_task.apply(
        args=(main_file.pk,),
        kwargs={"update_file_archive": update_file_archive, "update_link": False},
    )
    if eager_result_res_file.status != SUCCESS:
        logger.error(f"Failed to process resource file: pk = {main_file.pk}")
        logger.info("Resource %s: file validation task status=False", resource.pk)
        return False

    logger.info("Resource %s: file validation task status=True", resource.pk)
    return True


def _run_file_data_validation(resource: "Resource") -> None:
    logger.info("Resource %s: running file data validation task", resource.pk)
    Resource = apps.get_model("resources", "Resource")
    # Re-fetch full model instance instead of refresh_from_db(): Resource keeps
    # custom _cached_file relation cache, and stale main-file metadata can make
    # is_data_processable false right after file validation updated ResourceFile.
    resource: "Resource" = Resource.raw.get(pk=resource.pk)
    # Note: this _may_ also schedule increase_openness_score_task
    resource.revalidate_tabular_data(apply_on_commit=False)
    logger.info("Resource %s: file data validation task finished", resource.pk)


def _schedule_es_and_rdf_update(resource: "Resource") -> None:
    logger.info("Resource %s: scheduling ES/RDF update", resource.pk)
    resource.refresh_from_db()
    resource.update_es_and_rdf_db()
    logger.info("Resource %s: ES/RDF update scheduling finished", resource.pk)


@extended_shared_task(
    ignore_result=True,
    # TODO(OTD-1446): Tasks' names aren't necessarily the same as import paths - check with Celery logs
    name="mcod.resources.tasks.entrypoint_process_resource_validation_task",
)
def entrypoint_process_resource_validation_task(
    resource_pk: int,
    update_verification_date: bool = True,
    update_file_archive: bool = False,
    forced_file_changed: bool = False,
) -> None:
    logger.info(
        "entrypoint_process_resource_validation_task started: resource_pk=%s update_verification_date=%s "
        "update_file_archive=%s forced_file_changed=%s",
        resource_pk,
        update_verification_date,
        update_file_archive,
        forced_file_changed,
    )
    set_tag("resource_id", str(resource_pk))
    from mcod.resources.models import RESOURCE_TYPE_API, RESOURCE_TYPE_FILE

    Resource = apps.get_model("resources", "Resource")
    deferred_exceptions = []

    # 1. Run url validation task
    url_validation_succeeded = False
    with report_exceptions("Exception occurred during url validation task", suppress=True):
        url_validation_succeeded = _run_url_validation(resource_pk, forced_file_changed)
    if not url_validation_succeeded:
        logger.error(f"Failed to process resource: pk = {resource_pk}")

    resource: Optional["Resource"] = None
    with report_exceptions(
        f"Exception occurred while loading resource: pk = {resource_pk}",
        suppress=True,
    ) as errors:
        resource = Resource.raw.get(pk=resource_pk)
    deferred_exceptions.extend(errors)
    logger.info("Resource %s: loaded resource object=%s", resource_pk, bool(resource))

    should_validate_file = bool(resource) and (
        resource.type == RESOURCE_TYPE_FILE or (resource.type == RESOURCE_TYPE_API and resource.forced_file_type)
    )
    logger.info("Resource %s: should_validate_file=%s", resource_pk, should_validate_file)

    # 2. Run file validation task
    file_validation_succeeded = False
    if should_validate_file and url_validation_succeeded and not deferred_exceptions:
        with report_exceptions("Exception occurred during file validation task", suppress=True):
            file_validation_succeeded = _run_file_validation(resource, update_file_archive)

    # 3. Run file data validation task
    if should_validate_file and url_validation_succeeded and file_validation_succeeded and not deferred_exceptions:
        with report_exceptions(
            "Exception occurred during file data validation task",
            suppress=True,
        ) as errors:
            _run_file_data_validation(resource)
        deferred_exceptions.extend(errors)

    # 4. Update openness and verification values in DB *before* scheduling ES/RDF update,
    # so that the ES worker reads the already-correct openness_score from the DB.
    with report_exceptions("Exception occurred during openness score update"):
        update_resource_openness_score(resource_pk)

    if update_verification_date:
        with report_exceptions("Exception occurred during verification date update"):
            update_resource_verification_date(resource_pk)

    # 5. Schedule ES/RDF update (only when the whole pipeline succeeded).
    if url_validation_succeeded and not deferred_exceptions and (not should_validate_file or file_validation_succeeded):
        with report_exceptions(
            "Exception occurred during ES/RDF update scheduling",
            suppress=True,
        ) as errors:
            _schedule_es_and_rdf_update(resource)
        deferred_exceptions.extend(errors)

    if deferred_exceptions:
        deferred_exc = deferred_exceptions[0]
        logger.error(f"Exception occurred during process_resource_validation_task: {deferred_exc}")
        raise deferred_exc

    logger.info("entrypoint_process_resource_validation_task finished: resource_pk=%s", resource_pk)
