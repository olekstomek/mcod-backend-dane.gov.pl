import csv
import logging
import os

import pandas as pd
import sentry_sdk
import uuid
import datetime
from mimetypes import guess_type
from typing import List, Optional, Tuple, Union, Set

from cache_memoize import cache_memoize
from celery import states
from chardet import detect as detect_encoding
from django.apps import apps
from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.files.uploadedfile import (
    InMemoryUploadedFile,
    SimpleUploadedFile,
)
from django.db import transaction
from django.db.models import QuerySet

from mcod.core.utils import save_df_to_xlsx
from mcod.resources.dga_constants import DGA_COLUMNS
from mcod.resources.exceptions import (
    PendingValidationException,
    FailedValidationException,
)
from mcod.resources.goodtables_checks import ZERO_DATA_ROWS_MSG

logger = logging.getLogger('mcod')


def get_main_dga_resource() -> Optional["Resource"]:  # noqa: F821
    from mcod.resources.models import AggregatedDGAInfo
    dga_info: Optional[AggregatedDGAInfo] = AggregatedDGAInfo.objects.last()
    return dga_info.main_dga_resource if dga_info else None


def get_main_dga_dataset() -> Optional["Dataset"]:  # noqa: F821
    from mcod.resources.models import AggregatedDGAInfo
    dga_info: Optional[AggregatedDGAInfo] = AggregatedDGAInfo.objects.last()
    return dga_info.main_dga_dataset if dga_info else None


def validate_dga_file_columns(file: InMemoryUploadedFile, extension: str) -> bool:
    try:
        if extension in ("xls", "xlsx"):
            df = pd.read_excel(file)
        elif extension == "csv":
            raw_data = file.read()
            file.seek(0)
            result = detect_encoding(raw_data)
            encoding = result['encoding']
            if encoding is None:
                logger.error("Could not detect dga file encoding")
                return False

            content = raw_data.decode(encoding)
            dialect = csv.Sniffer().sniff(content)
            df = pd.read_csv(file, dialect=dialect, nrows=1)
        else:
            return False

        return df.columns.to_list() == DGA_COLUMNS
    except Exception as e:
        logger.exception(f"Error reading dga file: {e}")
        return False


def get_dga_resource_for_institution(
        organization_id: Union[int, str],
        exclude_resource_id: Optional[Union[int, str]] = None,
) -> Optional["Resource"]:  # noqa: F821
    """
    Returns DGA Resource object for given Organization. Main DGA Resource
    and Resource object with given PK are excluded.
    """
    from mcod.resources.models import Resource

    # Exclude main DGA Resource and Resource with given id
    exclude_objects_ids: List[Union[int, str]] = []
    main_dga_resource: Optional[Resource] = get_main_dga_resource()

    if main_dga_resource:
        exclude_objects_ids.append(main_dga_resource.pk)

    if exclude_resource_id:
        exclude_objects_ids.append(exclude_resource_id)

    query = Resource.objects.filter(
        dataset__organization=organization_id,
        contains_protected_data=True,
        status="published"
    ).exclude(id__in=exclude_objects_ids)

    count_dga_resources: int = query.count()
    if count_dga_resources > 1:
        error_message = (
            f"Found {count_dga_resources} DGA Resources for organization: "
            f"{organization_id}"
        )
        logger.error(error_message)
        raise MultipleObjectsReturned(error_message)

    return query.first()


def create_uploaded_file_from_path(path: str) -> Union[
    SimpleUploadedFile, None
]:
    try:
        with open(path, 'rb') as tmp_file:
            file_content = tmp_file.read()

        file_name = os.path.basename(path)
        content_type, _ = guess_type(path)
        file = SimpleUploadedFile(
            name=file_name,
            content=file_content,
            content_type=content_type,
        )
    except FileNotFoundError:
        logger.error(f"Cannot find a file at {path}")
        return None
    except Exception as e:
        logger.error(
            f"Exception while uploading from path {path} occurred: {e}"
        )
        return None
    return file


def save_temp_dga_file(file: InMemoryUploadedFile) -> str:
    file_name = file.name
    base_name, extension = os.path.splitext(file_name)
    unique_id = uuid.uuid4()
    temp_file_name = f"{base_name}_{unique_id}{extension}"
    directory = settings.DGA_RESOURCE_CREATION_STAGING_ROOT
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, temp_file_name)

    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    return temp_file_name


def key_generator_for_create_main_xlsx_file(*args, **kwargs) -> str:
    return "main_xlsx_file_path_to_clean"


def get_or_create_main_dga_path() -> str:
    directory: str = settings.MAIN_DGA_RESOURCE_XLSX_CREATION_ROOT
    if not os.path.exists(directory):
        os.makedirs(directory)

    today_date: str = datetime.datetime.now().strftime("%Y%m%d")
    file_name: str = f"{settings.MAIN_DGA_XLSX_FILE_NAME_PREFIX} {today_date}.xlsx"
    file_path: str = f"{directory}/{file_name}"
    return file_path


def get_all_dga_resources() -> QuerySet:
    Resource = apps.get_model("resources", "Resource")

    # Exclude current main DGA Resource in file creation process.
    main_dga_resource: Optional[Resource] = get_main_dga_resource()
    main_dga_id = main_dga_resource.pk if main_dga_resource else None

    dga_resources = Resource.objects.filter(
        contains_protected_data=True, status="published"
    ).exclude(id=main_dga_id).select_related("dataset__organization")
    return dga_resources


def create_main_dga_df(resources: QuerySet) -> pd.DataFrame:
    main_dga_columns: List[str] = [
        "Nazwa dysponenta zasobu",
        "Zasób chronionych danych",
        "Format danych",
        "Rozmiar danych",
    ]
    main_df: pd.DataFrame = pd.DataFrame(columns=main_dga_columns)

    count_dga_resources: int = resources.count()
    successful_resource_reads: int = 0
    for resource in resources:
        try:
            data = resource.tabular_data.table.read(keyed=True)
        except Exception as e:
            logger.error(
                f"Cannot read tabular data for for resource {resource.pk}: {e}"
            )
            continue

        try:
            df: pd.DataFrame = pd.DataFrame(data, columns=main_df.columns)
        except Exception as e:
            logger.error(
                f"Cannot create DataFrame for resource {resource.pk}: {e}"
            )
            sentry_sdk.api.capture_exception(e)
            continue

        institution: str = resource.institution.title
        df["Nazwa dysponenta zasobu"] = institution

        main_df = pd.concat([main_df, df], ignore_index=True)
        successful_resource_reads += 1

    logger.info(
        f"Successful DGA Resources read: "
        f"{successful_resource_reads}/{count_dga_resources}."
    )

    if main_df.empty:
        logger.warning("Empty main DGA file.")

    # Insert a new column "Lp." at the first position in the DataFrame.
    # The column contains a sequence of numbers starting from 1 to the length
    # of the DataFrame.
    main_df.insert(0, "Lp.", range(1, len(main_df) + 1))

    # Add a new column "Warunki ponownego wykorzystywania" to the DataFrame.
    # Every row in this column is set to the string "określone w ofercie".
    main_df["Warunki ponownego wykorzystywania"] = "określone w ofercie"

    return main_df


@cache_memoize(
    timeout=settings.MAIN_DGA_RESOURCE_XLSX_CREATION_CACHE_TIMEOUT,
    hit_callable=lambda *args, **kwargs: logger.info(
        "Using cache for main DGA file path."
    ),
    key_generator_callable=key_generator_for_create_main_xlsx_file,
)
def create_main_dga_file() -> str:
    """
    Creates the main DGA XLSX file based on all DGA resources.

    This function creates an XLSX file that contains information about all
    DGA resources. The file is saved to the file system, and the path to the
    created file is returned.

    Returns:
        str: The path to the created XLSX file.
    """
    file_path: str = get_or_create_main_dga_path()
    dga_resources: QuerySet = get_all_dga_resources()
    main_df: pd.DataFrame = create_main_dga_df(dga_resources)

    sheet_name: str = settings.MAIN_DGA_XLSX_WORKSHEET_NAME
    save_df_to_xlsx(df=main_df, file_path=file_path, sheet_name=sheet_name)
    return file_path


def check_all_resource_validations_status(resource: "Resource") -> None:  # noqa: F821
    """
    Checks the validation status of all tasks associated with the given
    resource.

    This function refreshes the resource from the database to ensure it has the
    latest data.
    It then checks the status of data tasks, file tasks, and link tasks
    associated with the resource.

    Args:
        resource (Resource): The resource object whose task statuses are to be
        checked.

    Raises:
        PendingValidationException: If any of the task validations are still
        pending.

        FailedValidationException: If any of the task validations are failed
        except for the validation of the empty file data task.
    """
    resource.refresh_from_db()
    data_task_status: str = resource.data_tasks_last_status
    file_task_status: str = resource.file_tasks_last_status
    link_task_status: str = resource.link_tasks_last_status

    statuses = {
        "data": data_task_status,
        "file": file_task_status,
        "link": link_task_status,
    }

    # All validations succeeded
    if all(status == states.SUCCESS for status in statuses.values()):
        logger.info(f"All validation for resource {resource.pk} succeeded.")
        return

    # Raise FailedValidation when file or link validation failed
    if any(status == states.FAILURE for status in
           [statuses["file"], statuses["link"]]):
        logger.error(
            f"Validation(s) for resource {resource.pk} failed: "
            f"data: {statuses['data']}; "
            f"file: {statuses['file']}; "
            f"link: {statuses['link']}."
        )
        raise FailedValidationException

    # Don't raise exception if the only reason for data validation failure
    # is an empty file
    if statuses["data"] == states.FAILURE:
        from mcod.resources.models import TaskResult
        data_task: Optional[TaskResult] = resource.data_tasks.last()
        data_failure_msg: Optional[
            List[str]] = data_task.message if data_task else None

        if data_failure_msg == [ZERO_DATA_ROWS_MSG]:
            if all(
                status == states.SUCCESS for status in [
                    statuses["file"], statuses["link"]
                ]
            ):
                return
        else:
            logger.error(f"Data validation for resource {resource.pk} failed.")
            raise FailedValidationException

    # Raise PendingValidation exception in other scenarios
    logger.info(
        f"Pending validation(s) for resource {resource.pk}: "
        f"data: {statuses['data']}; "
        f"file: {statuses['file']}; "
        f"link: {statuses['link']}."
    )
    raise PendingValidationException


def get_default_main_dga_dataset_categories() -> List["Category"]:  # noqa: F821
    """
    Retrieves the main DGA dataset categories based on the titles specified in
    the settings. If a category with a specified title is not found, a warning
    is logged.
    """
    Category = apps.get_model("categories", "Category")
    categories_titles: List[str] = settings.MAIN_DGA_DATASET_CATEGORIES_TITLES

    found_categories: QuerySet = Category.objects.filter(
        title__in=categories_titles
    )
    found_titles: Set[str] = set(
        category.title for category in found_categories
    )

    missing_titles: Set[str] = set(categories_titles) - found_titles
    for missing_title in missing_titles:
        logger.warning(f"No category with title {missing_title} found.")

    return list(found_categories)


def get_or_create_default_main_dga_dataset_tags() -> List["Tag"]:  # noqa: F821
    """
    Retrieves or creates the main DGA dataset tags based on the names specified
    in the settings.
    """
    Tag = apps.get_model("tags", "Tag")
    tags_names: List[str] = settings.MAIN_DGA_DATASET_TAGS_NAMES
    pl_lang = settings.LANGUAGES[0][0]

    tags = []
    for tag_name in tags_names:
        tag, created = Tag.objects.get_or_create(
            name=tag_name, language=pl_lang
        )
        if created:
            logger.info(f"Created Tag with name {tag_name}.")
        tags.append(tag)

    return tags


def create_main_dga_dataset() -> int:
    """
    Creates the main DGA Dataset for the 'Ministerstwo Cyfryzacji' institution.

    Returns:
        int: The primary key of the newly created Dataset.

    Raises:
        ObjectDoesNotExist: If the Institution is not found.
    """
    Organization = apps.get_model("organizations", "Organization")
    Dataset = apps.get_model("datasets", "Dataset")
    Category = apps.get_model("categories", "Category")
    Tag = apps.get_model("tags", "Tag")

    # Get "Ministerstwo Cyfryzacji" institution object who is the owner of the
    # main DGA Dataset
    organization_pk: int = settings.MAIN_DGA_DATASET_OWNER_ORGANIZATION_PK
    try:
        institution: Organization = Organization.objects.get(
            pk=organization_pk
        )
    except Organization.DoesNotExist:
        logger.error(
            f"Can't create main DGA dataset. "
            f"Institution with pk {organization_pk} not found."
        )
        raise ObjectDoesNotExist("Main DGA Owner Institution not found.")

    dataset_params = {
        "title": settings.MAIN_DGA_DATASET_DEFAULT_TITLE,
        "notes": settings.MAIN_DGA_DATASET_DEFAULT_DESC,
        "organization": institution,
        "update_notification_recipient_email": settings.MAIN_DGA_DATASET_UPDATE_NOTIFICATION_EMAIL,
        "has_dynamic_data": False,
        "has_high_value_data": False,
        "has_research_data": False,
        "update_frequency": "daily",
        "status": "published",
    }

    with transaction.atomic():
        dataset = Dataset.objects.create(**dataset_params)

        categories: List[Category] = get_default_main_dga_dataset_categories()
        tags: List[Tag] = get_or_create_default_main_dga_dataset_tags()

        dataset.categories.set(categories)
        dataset.tags.set(tags)
        dataset.save()

    logger.info(f"Created main DGA dataset {dataset.pk}.")
    return dataset.pk


def key_generator_for_create_main_dga_resource(*args, **kwargs) -> str:
    return "main_dga_to_clean"


@cache_memoize(
    timeout=settings.MAIN_DGA_RESOURCE_CREATION_CACHE_TIMEOUT,
    hit_callable=lambda *args, **kwargs: logger.info(
        "DGA objects get from cache."
    ),
    key_generator_callable=key_generator_for_create_main_dga_resource,
)
def create_main_dga_resource_with_dataset(
        file_path: str
) -> Tuple[int, Optional[int]]:
    """
    Creates the main DGA Resource, including related ResourceFile objects and
    the main DGA Dataset for the `Ministerstwo Cyfryzacji` institution if it
    does not already exist.

    Args:
        file_path (str): The path to the XLSX file to be used for the Resource.

    Returns:
        int: The primary key of the newly created Resource.
        Optional[int]: The Dataset primary key if created.
    """
    # Import models due to circular imports
    Resource = apps.get_model("resources", "Resource")
    ResourceFile = apps.get_model("resources", "ResourceFile")
    Dataset = apps.get_model("datasets", "Dataset")

    # Get info about current main DGA Resource and Dataset
    old_main_dga_resource: Optional[Resource] = get_main_dga_resource()
    main_dga_dataset: Optional[Dataset] = get_main_dga_dataset()

    # Create Resource and ResourceFile objects.
    new_main_dga_dataset_created: bool = False
    with transaction.atomic():
        # Create main DGA Dataset if it does not exist
        if main_dga_dataset is None:
            main_dga_dataset_pk: int = create_main_dga_dataset()
            new_main_dga_dataset_created = True
            main_dga_dataset: Dataset = Dataset.objects.get(
                pk=main_dga_dataset_pk
            )

        # Get metadata from existing resource or assign new one
        if old_main_dga_resource:
            title: str = old_main_dga_resource.title
            description: str = old_main_dga_resource.description
        else:
            title = settings.MAIN_DGA_RESOURCE_DEFAULT_TITLE
            description = settings.MAIN_DGA_RESOURCE_DEFAULT_DESC

        resource_params = {
            "title": title,
            "description": description,
            "dataset": main_dga_dataset,
            "has_dynamic_data": False,
            "has_high_value_data": False,
            "has_research_data": False,
            "contains_protected_data": True,
            "status": "published",
            "data_date": datetime.datetime.today(),
        }

        with open(file_path, "rb") as file:
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            file_name = os.path.basename(file.name)
            django_file = SimpleUploadedFile(
                name=file_name, content=file.read(), content_type=mimetype
            )
            resource = Resource.objects.create(**resource_params)
            logger.debug(f"Created Main DGA resource {resource.pk}")

            # this will run post_save signal which runs all validation tasks
            resource_file = ResourceFile.objects.create(
                resource=resource, is_main=True, file=django_file
            )
            logger.debug(f"Created Main DGA resource file {resource_file.pk}")

    return (
        resource.pk,
        main_dga_dataset.pk if new_main_dga_dataset_created else None,
    )


def update_or_create_aggr_dga_info_and_delete_old_main_dga(
        new_main_dga_resource: "Resource"  # noqa: F821
) -> None:
    """
    Updates or creates an entry in the AggregatedDGAInfo table with the new
    main DGA Resource.

    This function updates the existing entry in the AggregatedDGAInfo table
    to reference the new main DGA Resource. If no such entry exists,
    it creates a new one. Additionally, it deletes the old main DGA Resource
    to ensure that only one main DGA Resource is active at any given time.
    """
    Resource = apps.get_model("resources", "Resource")
    AggregatedDGAInfo = apps.get_model("resources", "AggregatedDGAInfo")
    dga_info: Optional[AggregatedDGAInfo] = AggregatedDGAInfo.objects.last()
    old_main_dga_resource: Optional[
        Resource] = dga_info.main_dga_resource if dga_info else None

    with transaction.atomic():
        if dga_info:
            dga_info.resource = new_main_dga_resource
            dga_info.views_count = new_main_dga_resource.dataset.computed_views_count
            dga_info.downloads_count = new_main_dga_resource.dataset.computed_downloads_count
            dga_info.save()
            logger.info(
                f"Updated AggregatedDGAInfo: {dga_info.pk} with resource: "
                f"{new_main_dga_resource.pk}."
            )

        else:
            dga_info: AggregatedDGAInfo = AggregatedDGAInfo.objects.create(
                resource=new_main_dga_resource
            )
            logger.info(
                f"Created AggregatedDGAInfo: {dga_info.pk} with resource: "
                f"{new_main_dga_resource.pk}."
            )

        if old_main_dga_resource:
            old_main_dga_resource.delete()
            logger.info(
                f"Previous Main DGA Resource "
                f"{old_main_dga_resource.pk} deleted."
            )


def clean_up_after_main_dga_resource_creation(
        exception_occurred: bool
) -> None:
    """
    Cleans up objects created by the main_dga_resource_task only when it fails.
    This function will remove the Resource, ResourceFile and Dataset objects
    created during the task execution to maintain system integrity if
    exception_occurred is True. This function also remove created xlsx file
    from temp directory when task succeeded.
    """
    logger.info("Starting clean up process after main DGA Resource creation.")

    cache = caches["default"]
    clean_objects_key: str = key_generator_for_create_main_dga_resource()
    clean_file_path_key: str = key_generator_for_create_main_xlsx_file()

    resource_created: Optional[int]
    dataset_created: Optional[int]
    resource_created, dataset_created = cache.get(
        clean_objects_key, (None, None)
    )
    file_path: Optional[str] = cache.get(clean_file_path_key, None)

    # delete created objects and release cache
    try:
        if exception_occurred and resource_created:
            Resource = apps.get_model("resources", "Resource")
            Resource.raw.filter(pk=resource_created).delete()

        if exception_occurred and dataset_created:
            Dataset = apps.get_model("datasets", "Dataset")
            Dataset.raw.filter(pk=dataset_created).delete()

        cache.delete(clean_objects_key)

    except Exception as exc:
        logger.error(f"Clean up failed. Reason: {exc}")
        sentry_sdk.api.capture_exception(exc)

    # delete file and release cache
    try:
        if file_path:
            os.remove(file_path)
            logger.info(f"File {file_path} has been deleted successfully.")
            cache.delete(clean_file_path_key)

    except Exception as e:
        logger.error(
            f"An error occurred while deleting the file {file_path}: {e}"
        )

    logger.info("Clean up completed.")
