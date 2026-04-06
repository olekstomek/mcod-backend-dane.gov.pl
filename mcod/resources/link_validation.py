import logging
import os
from io import BytesIO
from mimetypes import MimeTypes
from typing import Tuple
from uuid import uuid4

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from fake_useragent import UserAgent
from mimeparse import MimeTypeParseException, parse_mime_type
from requests import Session

from mcod.lib.exceptions import (
    DangerousContentError,
    EmptyDocument,
    HTTPConnectionError,
    InvalidContentType,
    InvalidResponseCode,
    InvalidSchema,
    InvalidUrl,
    MissingContentType,
    UnsupportedContentType,
)
from mcod.lib.file_format_from_response import (
    _filename_from_url,
    get_extension_from_content_disposition,
    get_extension_from_mime_type,
    get_filename_from_content_disposition,
)
from mcod.resources import guess
from mcod.resources.file_validation import file_format_from_content_type_extension_map
from mcod.resources.geo import is_json_stat

logger = logging.getLogger("mcod")

mime = MimeTypes()

session = Session()


old_merge_environment_settings = requests.Session.merge_environment_settings


def _get_resource_type(response, api_content_types=("atom+xml", "vnd.api+json", "json", "xml")):
    _, content_type, _ = parse_mime_type(response.headers.get("Content-Type"))
    is_attachment = "attachment" in response.headers.get("Content-Disposition", "")
    if content_type == "html" and guess.web_format(response.content):
        return "website"
    elif not is_attachment and content_type in api_content_types and guess.api_format(response.content):
        return "api"
    return "file"


def content_type_from_file_format(file_format):
    results = list(filter(lambda x: file_format in x[2], settings.CONTENT_TYPE_TO_EXTENSION_MAP))
    if not results:
        return None, None

    return results[0][0], results[0][1]


def simplified_url(url):
    return url.replace("http://", "").replace("https://", "").replace("www.", "").rstrip("/")


def generate_random_user_agent() -> str:
    return UserAgent(min_percentage=5.0).random


def download_file(url, forced_file_type=False) -> Tuple[str, dict]:  # noqa: C901
    logger.debug(f"Starting downloading file in download_file function ({url})")
    try:
        URLValidator()(url)
    except ValidationError:
        raise InvalidUrl(f"Invalid url address: {url}")

    filename, _format = None, None

    headers = {"User-Agent": generate_random_user_agent()}
    response = session.get(
        url,
        stream=True,
        allow_redirects=True,
        verify=False,
        timeout=settings.HTTP_REQUEST_DEFAULT_TIMEOUT,
        headers=headers,
    )

    if not response.url.startswith("https"):
        raise InvalidSchema("Invalid schema!")
    if response.status_code != 200:
        raise InvalidResponseCode(f"Invalid response code: {response.status_code}")
    if "Content-Type" not in response.headers:
        raise MissingContentType("Missing content-type header")
    try:
        family, content_type, options = parse_mime_type(response.headers.get("Content-Type"))
    except MimeTypeParseException:
        raise InvalidContentType(response.headers.get("Content-Type"))

    logger.debug(f"  Content-Type: {family}/{content_type};{options}")

    if not guess.is_octetstream(content_type) and content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise UnsupportedContentType(f"Unsupported type: {response.headers.get('Content-Type')}")

    try:
        # Get resource type from Content-Type and Content-Disposition. Default is `file`
        resource_type = _get_resource_type(response)
        if resource_type == "api" and forced_file_type:
            logger.debug("Forcing file type")
            resource_type = "file"
    except Exception as exc:
        if str(exc) == "Document is empty":
            raise EmptyDocument("Document is empty")
        raise exc
    logger.debug(f"  resource_type: {resource_type}")
    options = {"response": response}

    content = BytesIO(response.content)
    if resource_type == "file":
        content_disposition = response.headers.get("Content-Disposition", None)
        logger.debug(f"  content_disposition: {content_disposition}")
        if content_disposition:
            filename = get_filename_from_content_disposition(response.headers)
            _format = get_extension_from_content_disposition(response.headers)
        if not filename:
            name, _format_from_url = _filename_from_url(url)
            _format_from_content_type = get_extension_from_mime_type(content_type)
            logger.debug(f"  filename: {name}, {_format_from_url=}, {_format_from_content_type=}")
            _format = _format_from_url or _format_from_content_type
            filename = ".".join([name, _format])

        if content_disposition and "attachment" in content_disposition and _format in settings.RESTRICTED_FILE_TYPES:
            raise DangerousContentError(
                f"Dangerous content: restricted file type: {_format}"
            )  # https://cwe.mitre.org/data/definitions/434.html
        filename = filename.strip(".")

        if guess.is_octetstream(content_type):
            family, content_type = content_type_from_file_format(_format)
            logger.debug(f"  {family}/{content_type} - from file format")

        _format = file_format_from_content_type_extension_map(content_type, family=family, extension=_format)
        logger.debug(f"  format:{_format} - from content type (file)")
        options.update(
            {
                "filename": add_unique_suffix_to_filename(filename),
                "format": _format,
                "content": content,
            }
        )
    else:
        _format = file_format_from_content_type_extension_map(content_type, family)
        logger.debug(f"  format: {_format} - from content type (web/api)")
        if (
            resource_type != "api"
            and response.history
            and all(
                (
                    response.history[-1].status_code == 301,
                    simplified_url(response.url) != simplified_url(url),
                )
            )
        ):
            raise InvalidResponseCode("Resource location has been moved!")
        options.update({"format": _format})
    if format == "json" and is_json_stat(content):
        options["format"] = "jsonstat"
    return resource_type, options


def add_unique_suffix_to_filename(filename: str) -> str:
    """Create a new filename with added a unique suffix."""
    unique_suffix = uuid4().hex[:8]
    name, ext = os.path.splitext(filename)
    final_filename = f"{name}_{unique_suffix}" + ext
    logger.debug(f"  final unique filename with added suffix: {final_filename}")
    return final_filename


def check_link_scheme(link):
    change_required = False
    try:
        response = requests.get(link, allow_redirects=True, timeout=30, stream=True)
        returns_https = response.url.startswith("https")
    except Exception:
        returns_https = False
    if not returns_https:
        try:
            response = requests.get(
                link.replace("http://", "https://"),
                allow_redirects=True,
                timeout=30,
                stream=True,
            )
            response.raise_for_status()
            change_required = True
        except Exception:
            pass
    return returns_https, change_required


def check_link_status(url, resource_type):  # noqa: C901
    logger.debug(f"check_link_status({url})")
    try:
        URLValidator()(url)
    except ValidationError:
        raise InvalidUrl(f"Invalid url address: {url}")

    headers = {"User-Agent": generate_random_user_agent()}
    timeout = (5, 15)  # connect 5s, read 15s

    try:
        # HEAD
        with session.head(url, allow_redirects=True, timeout=timeout, headers=headers) as response:
            status = response.status_code
            head_headers = response.headers
            head_history = response.history
            head_url = response.url
        # GET
        if status != 200:
            with session.get(url, allow_redirects=True, timeout=timeout, headers=headers, stream=True) as response:
                status = response.status_code
                head_headers = response.headers
                head_history = response.history
                head_url = response.url
    except requests.exceptions.Timeout as exc:
        raise HTTPConnectionError(f"Timeout while fetching: {url}") from exc

    except requests.exceptions.ConnectionError as exc:
        raise HTTPConnectionError(f"Connection error while fetching: {url}") from exc

    if status != 200:
        raise InvalidResponseCode(f"Invalid response code: {status}")

    try:
        family, content_type, options = parse_mime_type(head_headers.get("Content-Type"))
    except MimeTypeParseException:
        raise InvalidContentType(head_headers.get("Content-Type"))

    if not guess.is_octetstream(content_type) and content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise UnsupportedContentType(f"Unsupported type: {head_headers.get('Content-Type')}")

    if (
        resource_type not in ["file", "api"]
        and head_history
        and head_history[-1].status_code == 301
        and simplified_url(head_url) != simplified_url(url)
    ):
        raise InvalidResponseCode("Resource location has been moved!")
