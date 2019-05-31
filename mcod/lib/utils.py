# -*- coding: utf-8 -*-
import logging

import libarchive
import magic
import os
import re
import requests
import shapefile

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from io import BytesIO
from mimeparse import parse_mime_type
from mimetypes import MimeTypes
from urllib import parse

from mcod.lib import guess
from mcod.lib.hacks.goodtables import patch

patch.apply()  # noqa: E402

mime = MimeTypes()

logger = logging.getLogger('mcod')


class InvalidUrl(Exception):
    pass


class InvalidResponseCode(Exception):
    pass


class InvalidContentType(Exception):
    pass


def file_format_from_content_type(content_type, family=None, extension=None):
    if family:
        results = list(filter(
            lambda x: x[0] == family and x[1] == content_type,
            settings.SUPPORTED_CONTENT_TYPES))
    else:
        results = list(filter(
            lambda x: x[1] == content_type,
            settings.SUPPORTED_CONTENT_TYPES))

    if not results:
        return None

    content_item = results[0]

    if extension and extension in content_item[2]:
        return extension

    return content_item[2][0]


def content_type_from_file_format(file_format):
    results = list(filter(lambda x: file_format in x[2], settings.SUPPORTED_CONTENT_TYPES))
    if not results:
        return None, None

    return results[0][0], results[0][1]


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


def _get_resource_type(response):
    _, content_type, _ = parse_mime_type(response.headers.get('Content-Type'))

    if content_type == 'html' and guess.web_format(response, None):
        return 'website'

    if content_type in ('xml', 'json', 'vnd.api+json') and guess.api_format(response, None):
        return 'api'

    return 'file'


def simplified_url(url):
    return url.replace('http://', '').replace('https://', '').replace('www.', '').rstrip('/')


def download_file(url, allowed_content_types=None):  # noqa: C901
    logger.debug(f"download_file({url}, {allowed_content_types})")
    try:
        URLValidator()(url)
    except ValidationError:
        raise InvalidUrl('Invalid url address: %s' % url)

    filename, format = None, None

    supported_content_types = allowed_content_types or [ct[1] for ct in settings.SUPPORTED_CONTENT_TYPES]

    r = requests.get(url, stream=True, allow_redirects=True, verify=False, timeout=180)

    if r.status_code != 200:
        raise InvalidResponseCode('Invalid response code: %s' % r.status_code)

    family, content_type, options = parse_mime_type(r.headers.get('Content-Type'))
    logger.debug(f'  Content-Type: {family}/{content_type};{options}')

    if not guess.is_octetstream(content_type) and content_type not in supported_content_types:
        raise InvalidContentType('Unsupported type: %s' % r.headers.get('Content-Type'))

    resource_type = _get_resource_type(r)
    logger.debug(f'  resource_type: {resource_type}')

    if resource_type == 'file':
        content_disposition = r.headers.get('Content-Disposition', None)
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

        content = BytesIO(r.content)
        return resource_type, {
            'filename': filename,
            'format': format,
            'content': content
        }
    else:
        format = file_format_from_content_type(content_type, family)
        logger.debug(f'  format: {format} - from content type (web/api)')
        if resource_type == 'api':
            return resource_type, {
                'format': format
            }
        else:
            if all((r.history,
                    r.history[-1].status_code == 301,
                    simplified_url(r.url) != simplified_url(url))):
                raise InvalidResponseCode('Resource location has been moved!')
            return resource_type, {
                'format': format
            }


def cut_extension(filename):
    return filename.rsplit('.', 1)


def extract_resource(source, destiny_path=None):
    root_dir = destiny_path or '/'.join(source.split('/')[:-1])

    def full_path(local_path):
        return '/'.join((root_dir, str(local_path)))

    def deep_mkdir(dir_path):
        steps = dir_path.split('/')
        for i in range(len(steps)):
            step = '/'.join((root_dir, *(s for s in steps[:i+1] if s)))
            if not os.path.isdir(step):
                os.mkdir(step)

    files = []

    with libarchive.file_reader(source) as arch:
        for entry in arch:
            if entry.isdir:
                deep_mkdir(str(entry))
            else:
                path = str(entry).rsplit('/', 1)
                if len(path) > 1 and not os.path.isdir(full_path(path[0])):
                    deep_mkdir(path[0])
                resource_path = '/'.join((root_dir, *path))

                with open(resource_path, 'wb') as f:
                    for block in entry.get_blocks():
                        f.write(block)
                files.append(resource_path)

    return tuple(files)


def cleanup_extracted(files):
    dirs = set()
    for f in files:
        dirs.add('/'.join(f.split('/')[:-1]))
        os.remove(f)

    dirs = sorted(dirs, reverse=True)
    for d in dirs:
        try:
            os.rmdir(d)
        except OSError:
            pass


def _isnt_msdoc_text(content_type):
    try:
        extensions = next(filter(
            lambda x: x[1] == content_type,
            settings.SUPPORTED_CONTENT_TYPES)
        )[2]
        return len({'doc', 'docx'} & set(extensions)) == 0
    except StopIteration:
        return False


def _is_archive_file(content_type):
    return content_type in set(t[1] for t in settings.ARCHIVE_CONTENT_TYPES)


def _is_plain_text(family, content_type, extension):
    return family == 'text' and content_type == 'plain' or extension == 'zip'


def _isnt_text_encoding(encoding):
    return any((isinstance(encoding, str) and encoding.startswith('unknown'),
               encoding == 'binary',
               not encoding))


def _is_office_file(extension, content_type):
    return extension in ('doc', 'docx', 'xls', 'xlsx', 'ods', 'odt', 'zip') or content_type == 'msword'


def _is_spreadsheet(ext):
    return ext in ('xls', 'xlsx', 'ods')


def _are_shapefile(files):
    filenames = set(cut_extension(file)[0] for file in files)
    extensions = set(cut_extension(file)[-1] for file in files)
    return len(filenames) == 1 and len(extensions.intersection({'shp', 'shx', 'dbf'})) == 3


class UnknownFileFormatError(Exception):
    pass


class UnsupportedArchiveError(Exception):
    pass


def check_support(ext, content_type):
    if _is_office_file(ext, content_type):
        return
    try:
        next(filter(
            lambda x: x[1] == content_type,
            settings.SUPPORTED_CONTENT_TYPES)
        )
        return
    except StopIteration:
        if _is_archive_file(content_type):
            raise UnsupportedArchiveError('archives-are-not-supported')

    raise UnknownFileFormatError('unknown-file-format')


def _analyze_plain_text(path, extension, encoding):
    if encoding.startswith('unknown') or encoding == 'binary':
        encoding = guess.file_encoding(path)
        logger.debug(f" encoding (guess-plain): {encoding}")
    extension = guess.text_file_format(path, encoding) or extension
    logger.debug(f"  extension (guess-plain): {extension}")

    return extension, encoding


def _analyze_office_file(path, encoding, content_type, extension):
    tmp_extension = path.rsplit('.')[-1]
    if _isnt_text_encoding(encoding):
        encoding = guess.file_encoding(path)
        logger.debug(f"  encoding (guess-spreadsheet): {encoding}")
    tmp_encoding = encoding if encoding != 'binary' else 'unknown'
    spreadsheet_format = guess.spreadsheet_file_format(path, tmp_encoding)
    if all((_is_spreadsheet(tmp_extension),
            _isnt_msdoc_text(content_type),
            spreadsheet_format)):
        extension = spreadsheet_format
        logger.debug(f"  extension (guess-spreadsheet): {extension}")
    elif extension == 'zip' and encoding != 'binary':
        extension = tmp_extension

    return extension, encoding


def _analyze_shapefile(files):
    options = {}
    with shapefile.Reader(files[0]) as shp:
        options['charset'] = shp.encoding
        shp_type = shp.shapeTypeName

    return shp_type, options


def analyze_resource_file(path, extension=None):
    _magic = magic.Magic(mime=True, mime_encoding=True)

    def _parse_mime_type(path):
        result = _magic.from_file(path)
        return parse_mime_type(result)

    logger.debug(f"analyze_resource_file({path}, {extension})")
    family, content_type, options = _parse_mime_type(path)
    if _is_archive_file(content_type):
        extracted = extract_resource(path)
        if len(extracted) == 1:
            path = extracted[0]
            family, content_type, options = _parse_mime_type(path)
            logger.debug(f"  extracted file {path}")
        else:
            if _are_shapefile(extracted):
                shp_type, options = _analyze_shapefile(extracted)
                extension = 'shp'
                content_type = 'shapefile'
                logger.debug(f"  recognized shapefile {shp_type}, {options}")
            cleanup_extracted(extracted)

    logger.debug(f"  parsed mimetype: {family}/{content_type});{options}")
    file_info = magic.from_file(path)
    logger.debug(f"  file info: {file_info}")
    encoding = options.get('charset', 'unknown')
    logger.debug(f"  encoding: {encoding}")

    extension = file_format_from_content_type(content_type, family=family, extension=extension) or path.rsplit('.')[-1]
    logger.debug(f"  extension: {extension}")
    if _is_plain_text(family, content_type, extension):
        extension, encoding = _analyze_plain_text(path, extension, encoding)
    if _is_office_file(extension, content_type):
        extension, encoding = _analyze_office_file(path, encoding, content_type, extension)

    logger.debug(f'  finally: extension = {extension}, file_info = {file_info}, encoding = {encoding}')

    check_support(extension, content_type)

    return extension, file_info, encoding, path
