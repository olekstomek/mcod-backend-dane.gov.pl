import csv
import logging
import os
import uuid
from mimetypes import guess_type
from typing import Union, Optional

from chardet import detect as detect_encoding
from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.core.files.uploadedfile import (
    InMemoryUploadedFile,
    SimpleUploadedFile,
)
from pandas import read_excel, read_csv

from mcod.resources.dga_constants import DGA_COLUMNS
from mcod.resources.models import Resource

logger = logging.getLogger('mcod')


def validate_dga_file_columns(file: InMemoryUploadedFile, extension: str) -> bool:
    try:
        if extension in ("xls", "xlsx"):
            df = read_excel(file)
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
            df = read_csv(file, dialect=dialect, nrows=1)
        else:
            return False

        return df.columns.to_list() == DGA_COLUMNS
    except Exception as e:
        logger.exception(f"Error reading dga file: {e}")
        return False


def get_dga_resource_for_institution(
        organization_id: Union[int, str],
        exclude_object_id: Optional[Union[int, str]] = None,
) -> Optional[Resource]:
    query = Resource.objects.filter(
        dataset__organization=organization_id,
        contains_protected_data=True,
        status="published"
    )

    if exclude_object_id is not None:
        query = query.exclude(pk=exclude_object_id)

    count_dga_files: int = query.count()
    if count_dga_files > 1:
        error_message = (
            f"Found {count_dga_files} dga_files for organization: "
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
