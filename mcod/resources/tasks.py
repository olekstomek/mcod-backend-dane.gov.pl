import json
import logging
from copy import deepcopy

import pytz
from django.apps import apps
from django.conf import settings
from django.utils.timezone import now
from elasticsearch.helpers.errors import BulkIndexError

from mcod.core.tasks import extended_shared_task
from mcod.resources.archives import ArchiveReader, UnsupportedArchiveError
from mcod.resources.file_validation import (
    PasswordProtectedArchiveError,
    UnknownFileFormatError,
)
from mcod.resources.indexed_data import (
    FileEncodingValidationError,
    ResourceDataValidationError,
)
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
    Resource = apps.get_model("resources", "Resource")
    resource = Resource.raw.get(id=resource_id)
    if resource.is_imported_from_ckan:
        logger.debug(
            f"External resource imported from {resource.dataset.source} cannot be processed!"
        )
        return {}

    if update_file:
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
            ResourceFile.objects.filter(pk=res_file.pk).update(
                file=res_file.save_file(options["content"], options["filename"])
            )
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
        qs.update(
            type=resource_type, format=options["format"], openness_score=openness_score
        )
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
            file=resource_file.save_file(
                resource_file.file, f"{resource_file.file_basename}.{format}"
            )
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
        process_resource_from_url_task.s(
            resource_id, update_file=False, **kwargs
        ).apply_async_on_commit()
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
        logger.debug(
            f"Updated data date for resource with id {resource_id} with date {current_dt}"
        )
        if res.type in ["api", "website"]:
            res.update_es_and_rdf_db()
        elif res.is_linked:
            process_resource_from_url_task.s(
                res.id, update_file_archive=True
            ).apply_async()
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
        logger.debug(
            f"Updating file details of ResourceFile[{res_file_id}] for Resource with id {rf.resource_id}"
        )
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
        logger.debug(
            f"ResourceFile[{res_file_id}] has more than 1 file compressed, skipping."
        )
    return results
