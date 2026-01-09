import logging
from typing import Optional

from django.utils.translation import gettext_lazy as _
from marshmallow import ValidationError
from mimeparse import MimeTypeParseException
from requests import Response
from requests.exceptions import ConnectionError

from mcod.lib.exceptions import (
    DangerousContentError,
    EmptyDocument,
    InvalidContentType,
    InvalidResponseCode,
    InvalidSchema,
    InvalidUrl,
    MissingContentType,
    ResourceFormatValidation,
    UnsupportedContentType,
)
from mcod.lib.file_format_from_response import get_resource_format_from_response
from mcod.resources.link_validation import download_file
from mcod.unleash import is_enabled

logger = logging.getLogger("mcod")


def get_and_validate_resource_format_from_response(url: str) -> Optional[str]:
    try:
        __, options = download_file(url)
    except (
        InvalidUrl,
        InvalidSchema,
        InvalidResponseCode,
        MissingContentType,
        InvalidContentType,
        UnsupportedContentType,
        MimeTypeParseException,
        EmptyDocument,
        DangerousContentError,
        ConnectionError,
    ) as exc:
        raise ValidationError(str(exc))
    except Exception as exc:
        logger.error(f"Error while download file from: {url}. Error: {exc}")
        raise ValidationError(_("Error while download file from: %(url)s.") % {"url": url})

    response: Response = options.get("response")
    raise_exception = True if is_enabled("harvester_file_validation.be") else False
    try:
        parsed_file_type = get_resource_format_from_response(response, raise_on_unsupported=raise_exception)
    except ResourceFormatValidation as exc:
        raise ValidationError(exc.message)
    return parsed_file_type
