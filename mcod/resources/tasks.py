import json
import logging
import os
from copy import deepcopy
from pathlib import Path
from typing import List, Set, Tuple, Union

import pytz
import sentry_sdk
from constance import config
from django.apps import apps
from django.conf import settings
from django.core.mail import send_mail
from django.utils.timezone import now
from django_elasticsearch_dsl import Index
from elasticsearch.exceptions import (
    ConnectionError as ElasticsearchConnectionError,
    ElasticsearchException,
)
from elasticsearch.helpers.errors import BulkIndexError
from urllib3.exceptions import NewConnectionError

from mcod.core.tasks import FIVE_MINUTES, extended_shared_task
from mcod.lib.db_utils import IndexConsistency, get_db_and_es_inconsistencies
from mcod.resources.archives import ArchiveReader, UnsupportedArchiveError
from mcod.resources.dga_utils import (
    check_all_resource_validations_status,
    clean_up_after_main_dga_resource_creation,
    create_main_dga_file,
    create_main_dga_resource_with_dataset,
    update_or_create_aggr_dga_info_and_delete_old_main_dga,
)
from mcod.resources.exceptions import FailedValidationException, PendingValidationException
from mcod.resources.file_validation import PasswordProtectedArchiveError, UnknownFileFormatError
from mcod.resources.indexed_data import FileEncodingValidationError, ResourceDataValidationError
from mcod.resources.link_validation import check_link_scheme

logger = logging.getLogger("mcod")


@extended_shared_task(ignore_result=False, atomic=True)
def process_resource_from_url_task(
    resource_id,
    update_file=True,
    update_file_archive=False,
    forced_file_changed=False,
    schedule_auto_data_date=False,
    cancel_auto_data_date=False,
    **kwargs,
):
    """
    Downloads and processes a file for a given resource ID.
    Note:
    - If the resource is imported from CKAN, it skips processing
        and returns an empty dictionary.
    - If 'update_file' is True, it downloads the file, determines the resource type, and
      calls 'process_for_separate_file_model' for further processing.
    """
    logger.info("Started process_resource_from_url_task task.")
    Resource = apps.get_model("resources", "Resource")
    resource = Resource.raw.get(id=resource_id)
    if resource.is_imported_from_ckan:
        logger.debug(f"External resource imported from {resource.dataset.source} cannot be processed!")
        return {}

    if update_file:
        logger.debug(f"Downloading file for resource: {resource.id}")
        resource_type, options = resource.download_file()
        if resource_type == "website" and resource.forced_api_type:
            logger.debug("Resource of type 'website' forced into type 'api'!")
            resource_type = "api"
        process_for_separate_file_model(
            resource_id,
            resource,
            options,
            resource_type,
            update_file_archive=update_file_archive,
            forced_file_changed=forced_file_changed,
            schedule_auto_data_date=schedule_auto_data_date,
            cancel_auto_data_date=cancel_auto_data_date,
            **kwargs,
        )

    resource = Resource.raw.get(id=resource_id)
    result = {
        "uuid": str(resource.uuid),
        "link": resource.link,
        "format": resource.format,
        "type": resource.type,
    }

    if resource.type == "file" and resource.main_file:
        result["path"] = resource.main_file.path
        result["url"] = resource.file_url

    return json.dumps(result)


def get_or_create_main_res_file(resource_id, openness_score):
    ResourceFile = apps.get_model("resources", "ResourceFile")

    try:
        res_file = ResourceFile.objects.get(resource_id=resource_id, is_main=True)
    except ResourceFile.DoesNotExist:
        res_file = ResourceFile.objects.create(
            resource_id=resource_id,
            openness_score=openness_score,
        )
    return res_file


def process_for_separate_file_model(
    resource_id,
    resource,
    options,
    resource_type,
    update_file_archive,
    forced_file_changed,
    schedule_auto_data_date,
    cancel_auto_data_date,
    **kwargs,
):
    process_auto_data_date = True
    Resource = apps.get_model("resources", "Resource")
    ResourceFile = apps.get_model("resources", "ResourceFile")
    openness_score, _ = resource.get_openness_score(options["format"])
    qs = Resource.raw.filter(id=resource_id)
    if resource_type == "file":
        res_file, created = ResourceFile.objects.get_or_create(
            resource_id=resource_id,
            is_main=True,
        )
        if "filename" in options:
            ResourceFile.objects.filter(pk=res_file.pk).update(file=res_file.save_file(options["content"], options["filename"]))
            qs.update(format=options["format"], openness_score=openness_score)
        process_auto_data_date = False
        process_resource_res_file_task.s(
            res_file.pk,
            update_link=False,
            update_file_archive=update_file_archive,
            schedule_auto_data_date=schedule_auto_data_date,
            cancel_auto_data_date=cancel_auto_data_date,
            **kwargs,
        ).apply_async_on_commit()
    else:  # API or WWW
        ResourceFile.objects.filter(resource_id=resource_id).delete()
        if forced_file_changed:
            resource.dataset.archive_files()
        qs.update(type=resource_type, format=options["format"], openness_score=openness_score)
    resource.refresh_from_db()
    if schedule_auto_data_date and process_auto_data_date:
        resource.schedule_data_date_update()
    elif cancel_auto_data_date and process_auto_data_date:
        resource.cancel_data_date_update()


@extended_shared_task(
    ignore_result=False,
    atomic=True,
    commit_on_errors=(ResourceDataValidationError, BulkIndexError),
)
def process_resource_file_data_task(resource_id, **kwargs):
    resource_model = apps.get_model("resources", "Resource")
    resource = resource_model.raw.get(id=resource_id)
    logger.info(f"process_resource_file_data_task: Resource {resource_id}")
    if not resource.is_data_processable:
        return json.dumps({})
    if not resource.data:
        raise Exception("Nieobsługiwany format danych lub błąd w jego rozpoznaniu.")
    tds = resource.tabular_data_schema
    if not tds or tds.get("missingValues") != resource.special_signs_symbols_list:
        tds = resource.data.get_schema(revalidate=True)
    if resource.from_resource and resource.from_resource.tabular_data_schema:
        old_fields = deepcopy(resource.from_resource.tabular_data_schema.get("fields"))
        for f in old_fields:
            if "geo" in f:
                del f["geo"]
        if tds.get("fields") == old_fields:
            tds = resource.from_resource.tabular_data_schema

    resource_model.objects.filter(pk=resource_id).update(tabular_data_schema=tds)
    resource = resource_model.objects.get(pk=resource_id)
    resource.data.validate()

    success, failed = resource.data.index(force=True)
    logger.info(f"process_resource_file_data_task: {success=}, {failed=}")

    return json.dumps(
        {
            "indexed": success,
            "failed": failed,
            "uuid": str(resource.uuid),
            "link": resource.link,
            "format": resource.format,
            "type": resource.type,
            "path": resource.main_file.path,
            "resource_id": resource_id,
            "url": resource.file_url,
        }
    )


@extended_shared_task
def send_resource_comment(resource_id, comment):
    model = apps.get_model("resources", "Resource")
    resource = model.objects.get(pk=resource_id)
    resource.send_resource_comment_mail(comment)
    return {"resource": resource_id}


@extended_shared_task
def update_resource_has_table_has_map_task(resource_id):
    resource_model = apps.get_model("resources", "Resource")
    obj = resource_model.raw.filter(id=resource_id).first()
    result = {"resource_id": resource_id}
    if obj:
        data = {}
        has_table = bool(obj.tabular_data)
        has_map = bool(obj.geo_data)
        if has_table != obj.has_table:
            data["has_table"] = has_table
        if has_map != obj.has_map:
            data["has_map"] = has_map
        if data:
            resource_model.raw.filter(id=resource_id).update(**data)
            result.update(data)
    return result


@extended_shared_task
def update_resource_validation_results_task(resource_id):
    resource_model = apps.get_model("resources", "Resource")
    obj = resource_model.raw.filter(id=resource_id).first()
    result = {"resource_id": resource_id}
    if obj:
        data = {}
        data_task = obj.data_tasks.last()
        file_task = obj.file_tasks.last()
        link_task = obj.link_tasks.last()
        if data_task:
            data["data_tasks_last_status"] = data_task.status
        if file_task:
            data["file_tasks_last_status"] = file_task.status
        if link_task:
            data["link_tasks_last_status"] = link_task.status
        if data:
            resource_model.raw.filter(id=resource_id).update(**data)
            result.update(data)
    return result


@extended_shared_task(ignore_result=False)
def validate_link(resource_id):
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


@extended_shared_task(ignore_result=False)
def check_link_protocol(resource_id, link, title, organization_title, resource_type):
    logger.debug(f"Checking link {link} of resource with id {resource_id}")
    returns_https, change_required = check_link_scheme(link)
    https_status = "NIE"
    if returns_https:
        https_status = "TAK"
    elif not returns_https and change_required:
        https_status = "Wymagana poprawa"
    return {
        "Https": https_status,
        "Id": resource_id,
        "Nazwa": title,
        "Typ": resource_type,
        "Instytucja": organization_title,
    }


@extended_shared_task
def process_resource_data_indexing_task(resource_id):
    resource_model = apps.get_model("resources", "Resource")
    obj = resource_model.objects.with_tabular_data(pks=[resource_id]).first()
    if obj:
        success, failed = obj.data.index(force=True)
        return {"resource_id": resource_id, "indexed": success, "failed": failed}
    return {}


@extended_shared_task(
    ignore_result=False,
    atomic=True,
    commit_on_errors=(
        FileEncodingValidationError,
        UnsupportedArchiveError,
        UnknownFileFormatError,
        PasswordProtectedArchiveError,
    ),
)
def process_resource_res_file_task(
    resource_file_id,
    update_link=True,
    update_file_archive=False,
    schedule_auto_data_date=False,
    cancel_auto_data_date=False,
    **kwargs,
):
    ResourceFile = apps.get_model("resources", "ResourceFile")
    Resource = apps.get_model("resources", "Resource")
    resource_file = ResourceFile.objects.get(pk=resource_file_id)
    resource_id = resource_file.resource_id
    (
        format,
        file_info,
        file_encoding,
        p,
        file_mimetype,
        analyze_exc,
        extracted_format,
        extracted_mimetype,
        extracted_encoding,
    ) = resource_file.analyze()
    if not resource_file.extension and format:
        ResourceFile.objects.filter(pk=resource_file_id).update(
            file=resource_file.save_file(resource_file.file, f"{resource_file.file_basename}.{format}")
        )
    ResourceFile.objects.filter(pk=resource_file_id).update(
        format=format,
        compressed_file_format=extracted_format,
        compressed_file_mime_type=extracted_mimetype,
        compressed_file_encoding=extracted_encoding,
        mimetype=file_mimetype,
        info=file_info,
        encoding=file_encoding,
    )
    resource = Resource.raw.get(pk=resource_id)
    Resource.raw.filter(pk=resource_id).update(
        format=format,
        type="file",
        link=resource.file_url if update_link else resource.link,
    )
    resource_file = ResourceFile.objects.get(id=resource_file_id)
    resource = Resource.raw.get(id=resource_id)
    format_ = extracted_format or format
    resource_score, files_score = resource.get_openness_score(format_)
    Resource.raw.filter(pk=resource_id).update(openness_score=resource_score)
    for rf in files_score:
        ResourceFile.objects.filter(pk=rf["file_pk"]).update(openness_score=rf["score"])

    if analyze_exc:
        raise analyze_exc

    resource_file.check_support()

    if resource_file.format == "csv" and resource_file.encoding is None:
        raise FileEncodingValidationError(
            [
                {
                    "code": "unknown-encoding",
                    "message": "Nie udało się wykryć kodowania pliku.",
                }
            ]
        )

    process_resource_file_data_task.s(resource_id, **kwargs).apply_async_on_commit()
    if update_link:
        process_resource_from_url_task.s(resource_id, update_file=False, **kwargs).apply_async_on_commit()
    if update_file_archive:
        resource.dataset.archive_files()
    if schedule_auto_data_date:
        resource.schedule_data_date_update()
    elif cancel_auto_data_date:
        resource.cancel_data_date_update()
    return json.dumps(
        {
            "uuid": str(resource.uuid),
            "link": resource.link,
            "format": resource_file.format,
            "type": resource.type,
            "path": resource_file.file.path,
            "url": resource.file_url,
        }
    )


@extended_shared_task
def update_data_date(resource_id):
    Resource = apps.get_model("resources", "Resource")
    res_q = Resource.objects.filter(pk=resource_id)
    res = res_q.first()
    if res.is_auto_data_date and res.is_auto_data_date_allowed:
        warsaw_tz = pytz.timezone(settings.TIME_ZONE)
        current_dt = now().astimezone(warsaw_tz).date()
        res_q.update(data_date=current_dt)
        logger.debug(f"Updated data date for resource with id {resource_id} with date {current_dt}")
        if res.type in ["api", "website"]:
            res.update_es_and_rdf_db()
        elif res.is_linked:
            process_resource_from_url_task.s(res.id, update_file_archive=True).apply_async()
        return {"current_date": current_dt}
    return {"current_date": None}


@extended_shared_task
def update_last_day_data_date(resource_id):
    update_data_date(resource_id)


@extended_shared_task
def update_resource_with_archive_format(res_file_id):
    ResourceFile = apps.get_model("resources", "ResourceFile")
    Resource = apps.get_model("resources", "Resource")
    rf = ResourceFile.objects.get(pk=res_file_id)
    extracted = ArchiveReader(rf.file.file.name)
    extracted_files = len(extracted)
    results = {
        "resource_id": rf.resource_id,
        "resource_file_id": res_file_id,
    }
    if extracted:
        extracted.cleanup()
    if extracted_files == 1:
        logger.debug(f"Updating file details of ResourceFile[{res_file_id}] for Resource with id {rf.resource_id}")
        (
            format,
            file_info,
            file_encoding,
            p,
            file_mimetype,
            analyze_exc,
            extracted_format,
            extracted_mimetype,
            extracted_encoding,
        ) = rf.analyze()
        ResourceFile.objects.filter(pk=res_file_id).update(
            format=format,
            mimetype=file_mimetype,
            encoding=file_encoding,
            compressed_file_format=extracted_format,
            compressed_file_mime_type=extracted_mimetype,
            compressed_file_encoding=extracted_encoding,
            info=file_info,
        )
        res = Resource.objects.filter(pk=rf.resource_id)
        obj = res.first()
        old_format = obj.format
        res.update(format=format)
        obj.update_es_and_rdf_db()
        results["old_format"] = old_format
        results["new_format"] = format
    else:
        logger.debug(f"ResourceFile[{res_file_id}] has more than 1 file compressed, skipping.")
    return results


@extended_shared_task
def clean_dga_temp_directory():
    logger.info("Cleaning DGA temp directory.")
    dga_temp_dir = settings.DGA_RESOURCE_CREATION_STAGING_ROOT
    if os.path.exists(dga_temp_dir):
        for filename in os.listdir(dga_temp_dir):
            file_path = os.path.join(dga_temp_dir, filename)
            try:
                logger.debug(f"Removing {file_path}")
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Removing {file_path} failed. Reason: {e}")
                sentry_sdk.api.capture_exception(e)


@extended_shared_task(
    max_retries=5,
    atomic=False,
    retry_countdown=20,
    retry_on_errors=(PendingValidationException,),
    bind=True,
)
def create_main_dga_resource_task(self) -> None:
    """
    Performs the creation and management of a main DGA Resource, divided into
    several key steps:

    1. Creation of an XLSX file containing information about all DGA resources.
    2. Creation of a Resource and a ResourceFile objects for the main DGA.
       This step also includes a check to ensure that the main DGA Dataset
       exists; if not, it is created at this point.
    3. Verification that all validation stages for the resource have been
       successfully completed. If any validation is pending, the task is
       retried according to the specified number of attempts for this task.
    4. Updating the information in the AggregatedDGAInfo table and removing the
       old Resource.

    Cleanup process:
    If the task encounters an unexpected error or if the resource does not pass
    all validations within the designated number of check attempts, the created
    Resource, ResourceFile and Dataset objects are deleted to maintain
    integrity.
    Cleans task's cache when the task succeeded.

    Raises:
        PendingValidationException: If there are still running Resource
        validation stages.

        FailedValidationException: If any Resource validation stage failed.

    Returns:
        None: Completes the task without returning any value.
    """
    logger.info("Starting main DGA resource creation.")
    Resource = apps.get_model("resources", "Resource")

    try:
        # Step 1: Main DGA file creation
        logger.info("Step 1/4: Creating Main DGA xlsx file.")
        file_path: Path = create_main_dga_file()

        # Step 2: Main DGA Resource creation
        # (also creates ResourceFile and Dataset if needed).
        logger.info("Step 2/4: Creating Main DGA resource with files.")
        new_main_dga_resource_pk: int
        new_main_dga_resource_pk, _ = create_main_dga_resource_with_dataset(file_path=file_path)
        new_main_dga_resource: Resource = Resource.objects.get(pk=new_main_dga_resource_pk)

        # Step 3: Check resource validations
        logger.info("Step 3/4: Checking resource validations.")
        check_all_resource_validations_status(new_main_dga_resource)

        # Step 4: Update Aggregated DGA Info and delete old main DGA Resource
        logger.info("Step 4/4: Updating AggregatedDGAInfo and deleting old Resource.")
        update_or_create_aggr_dga_info_and_delete_old_main_dga(new_main_dga_resource)

        logger.info("Main DGA Resource successfully created.")

        # Clean cache when task succeeded
        clean_up_after_main_dga_resource_creation(exception_occurred=False)

    # Clean created data if resource not validated on last retry or another
    # exception occurred
    except PendingValidationException:
        max_retries: int = self.max_retries
        retry: int = self.request.retries
        if retry == max_retries:
            logger.info("Cleaning after main DGA resource creation task due to " "still pending resource validation(s).")
            clean_up_after_main_dga_resource_creation(exception_occurred=True)
        raise

    except FailedValidationException:
        clean_up_after_main_dga_resource_creation(exception_occurred=True)
        raise

    except Exception as exc:
        logger.error(f"Cleaning after main DGA resource creation task due to " f"unexpected error: {exc}")
        clean_up_after_main_dga_resource_creation(exception_occurred=True)
        raise


def delete_index(index_name: str) -> bool:
    index = Index(index_name)
    if index.exists():
        result = index.delete()
        if result.get("acknowledged") is True:
            return True
    return False


@extended_shared_task(
    max_retries=5,
    atomic=False,
    retry_countdown=60,
    retry_on_errors=(ElasticsearchException,),
    bind=True,
)
def delete_es_resource_tabular_data_index(self, resource_ids: Union[int, List[int]]):
    """
    Task which removes tabular data index for resource when resource is permanently deleted.
    F.e. for resource with id=123 removed index will be `resource-123`.
    """
    logger.info("Started delete_es_resource_tabular_data_index task.")
    es_index_deleted: bool = False

    if isinstance(resource_ids, int):
        resource_ids: List[int] = [resource_ids]

    for resource_id in resource_ids:
        index_name = f"resource-{resource_id}"
        result = delete_index(index_name)
        if result:
            es_index_deleted = True
            logger.info(f"Tabular data index {index_name} deleted.")
    if not es_index_deleted:
        logger.info("No tabular data index deleted.")
    logger.info("Finished delete_es_resource_tabular_data_index task.")


@extended_shared_task(
    max_retries=5,
    retry_on_errors=(NewConnectionError, ElasticsearchConnectionError),
    retry_countdown=FIVE_MINUTES,
)
def compare_postgres_and_elasticsearch_consistency_task(models_to_check: Tuple[str]) -> None:
    """
    Compare the existence consistency between Postgres and ElasticSearch for
    given models. Send email with consistency check result.

    Args:
        models_to_check (Tuple[str]): A tuple of model identifiers to check for consistency.
            Each element should follow the pattern "<django_application_label>.<django_model_name>".
            Example: ("resources.Resource", "datasets.Dataset")
    """
    if not models_to_check:
        logger.info("No models to check consistency for.")
        return

    logger.info(f"Starting compare consistency between Postgres and ElasticSearch for: {models_to_check}")

    error_msg = ""  # errors details which will be sent as email message
    for model in models_to_check:
        app_label, model_name = model.split(".")
        try:
            db_and_es_inconsistencies: List[IndexConsistency] = get_db_and_es_inconsistencies(app_label, model_name)
        except Exception as e:
            logger.error(f"Could not check consistency for {model}: {e}")
            # Add info about failed consistency check to email error message.
            error_msg += f"Could not check consistency for {model}. Error details: {e}"
            continue

        for inconsistency in db_and_es_inconsistencies:
            only_db_model_ids: Set[int] = inconsistency.only_db_ids
            only_es_model_ids: Set[int] = inconsistency.only_es_ids

            if only_db_model_ids:
                error_msg += (
                    f"{len(only_db_model_ids)} {model_name} objects present in "
                    f"PostgreSQL but not in ElasticSearch index"
                    f" {inconsistency.index_name}.\n"
                )
                error_msg += f"{model_name} ids: {only_db_model_ids}\n\n"

            if only_es_model_ids:
                error_msg += (
                    f"{len(only_es_model_ids)} documents for {model_name} present in "
                    f"ElasticSearch index {inconsistency.index_name} but not in PostgreSQL.\n"
                )
                error_msg += f"{model_name} ids: {only_es_model_ids}\n\n"

    if error_msg:
        logger.info("Database and ElasticSearch are inconsistent or an exception occurred.")
    else:
        logger.info("Database and ElasticSearch are consistent.")

    # Send email
    email_message = error_msg or "Database and ElasticSearch are consistent."
    recipients: List[str] = settings.DB_ES_CONSISTENCY_EMAIL_RECIPIENTS.split(",")

    logger.info(f"Sending email to {recipients}.")
    send_mail(
        subject="Postgres and ElasticSearch consistency check - Otwarte Dane.",
        message=email_message,
        from_email=config.NO_REPLY_EMAIL,
        recipient_list=recipients,
    )
