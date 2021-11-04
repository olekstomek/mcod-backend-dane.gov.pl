import logging
import os
import re
from io import BytesIO
from mimetypes import MimeTypes
from urllib import parse

import requests
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from mimeparse import parse_mime_type, MimeTypeParseException

from mcod import settings
from mcod.resources.archives import ARCHIVE_CONTENT_TYPES
from mcod.resources import guess
from mcod.resources.file_validation import file_format_from_content_type
from mcod.resources.geo import is_json_stat
from mcod.unleash import is_enabled


logger = logging.getLogger('mcod')

mime = MimeTypes()

session = requests.Session()


old_merge_environment_settings = requests.Session.merge_environment_settings


class EmptyDocument(Exception):
    pass


class InvalidUrl(Exception):
    pass


class InvalidResponseCode(Exception):
    pass


class InvalidContentType(Exception):
    pass


class MissingContentType(Exception):
    pass


class UnsupportedContentType(Exception):
    pass


def _get_resource_type(response):
    _, content_type, _ = parse_mime_type(response.headers.get('Content-Type'))
    content_disposition = response.headers.get('Content-Disposition', None)

    if content_type == 'html' and guess.web_format(response, None):
        return 'website'
    elif not (content_disposition and 'attachment' in content_disposition) and content_type in (
        'vnd.api+json',
        'json',
        'xml'
    ) and guess.api_format(response, None):
        return 'api'
    else:
        return 'file'


def filename_from_url(url, content_type=None):
    f, ext = os.path.splitext(os.path.basename(parse.urlparse(url).path))
    f = f.strip('.') if f else ''
    ext = ext.strip('.') if ext else ''

    if not ext and content_type:
        ext = file_format_from_content_type(content_type)
        if not ext:
            ext = mime.guess_extension(content_type)
            ext = ext.strip('.') if ext else ''

    return f or 'unknown', ext


def content_type_from_file_format(file_format):
    results = list(filter(lambda x: file_format in x[2], settings.SUPPORTED_CONTENT_TYPES))
    if not results:
        return None, None

    return results[0][0], results[0][1]


def simplified_url(url):
    return url.replace('http://', '').replace('https://', '').replace('www.', '').rstrip('/')


def download_file(url, forced_file_type=False, allowed_content_types=None):  # noqa: C901
    logger.debug(f"download_file({url}, {allowed_content_types})")
    try:
        URLValidator()(url)
    except ValidationError:
        raise InvalidUrl('Invalid url address: %s' % url)

    filename, format = None, None

    supported_content_types = allowed_content_types or [ct[1] for ct in settings.SUPPORTED_CONTENT_TYPES]
    supported_content_types += ARCHIVE_CONTENT_TYPES
    response = session.get(url, stream=True, allow_redirects=True, verify=False, timeout=180)

    if response.status_code != 200:
        raise InvalidResponseCode('Invalid response code: %s' % response.status_code)
    if 'Content-Type' not in response.headers:
        raise MissingContentType()
    try:
        family, content_type, options = parse_mime_type(response.headers.get('Content-Type'))
    except MimeTypeParseException:
        raise InvalidContentType(response.headers.get('Content-Type'))

    logger.debug(f'  Content-Type: {family}/{content_type};{options}')

    if not guess.is_octetstream(content_type) and content_type not in supported_content_types:
        raise UnsupportedContentType('Unsupported type: %s' % response.headers.get('Content-Type'))

    try:
        resource_type = _get_resource_type(response)
        if is_enabled('S27_forced_file_type.be') and resource_type == 'api' and forced_file_type:
            logger.debug('Forcing file type')
            resource_type = 'file'
    except Exception as exc:
        if str(exc) == 'Document is empty':
            raise EmptyDocument('Document is empty')
        raise exc
    logger.debug(f'  resource_type: {resource_type}')

    content = BytesIO(response.content)
    if resource_type == 'file':
        content_disposition = response.headers.get('Content-Disposition', None)
        logger.debug(f'  content_disposition: {content_disposition}')
        if content_disposition:
            # Get filename from header
            res = re.findall("filename=(.+)", content_disposition)
            filename = res[0][:100] if res else None
            logger.debug(f'  filename: {filename}')
            if filename:
                filename = filename.replace('"', '')
                format = filename.split('.')[-1]
                logger.debug(f'  filename: {filename}, format: {format}')

        if not filename:
            name, format = filename_from_url(url, content_type)
            filename = '.'.join([name, format])
            logger.debug(f'  filename: {filename}, format: {format} - from url')

        filename = filename.strip('.')

        if guess.is_octetstream(content_type):
            family, content_type = content_type_from_file_format(format)
            logger.debug(f'  {family}/{content_type} - from file format')

        format = file_format_from_content_type(content_type, family=family, extension=format)
        logger.debug(f'  format:{format} - from content type (file)')
        options = {
            'filename': filename,
            'format': format,
            'content': content
        }
    else:
        format = file_format_from_content_type(content_type, family)
        logger.debug(f'  format: {format} - from content type (web/api)')
        if resource_type != 'api' and response.history and all((
                response.history[-1].status_code == 301,
                simplified_url(response.url) != simplified_url(url))):
            raise InvalidResponseCode('Resource location has been moved!')
        options = {'format': format}
    if format == 'json' and is_enabled('S35_jsonstat.be') and is_json_stat(content):
        options['format'] = 'jsonstat'
    return resource_type, options


def check_link_status(url, resource_type):
    logger.debug(f"check_link_status({url})")
    try:
        URLValidator()(url)
    except ValidationError:
        raise InvalidUrl('Invalid url address: %s' % url)
    supported_content_types = [ct[1] for ct in settings.SUPPORTED_CONTENT_TYPES]
    supported_content_types += ARCHIVE_CONTENT_TYPES
    response = session.head(url, allow_redirects=True, timeout=30)
    if response.status_code == 405:
        response = session.get(url, allow_redirects=True, timeout=30)

    if response.status_code != 200:
        raise InvalidResponseCode('Invalid response code: %s' % response.status_code)

    try:
        family, content_type, options = parse_mime_type(response.headers.get('Content-Type'))
    except MimeTypeParseException:
        raise InvalidContentType(response.headers.get('Content-Type'))

    if not guess.is_octetstream(content_type) and content_type not in supported_content_types:
        raise UnsupportedContentType('Unsupported type: %s' % response.headers.get('Content-Type'))

    if resource_type not in ['file', 'api'] and response.history and\
            all((response.history[-1].status_code == 301, simplified_url(response.url) != simplified_url(url))):
        raise InvalidResponseCode('Resource location has been moved!')
