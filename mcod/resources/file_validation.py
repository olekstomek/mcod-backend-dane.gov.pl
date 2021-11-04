import logging

import magic
from mimeparse import parse_mime_type

from mcod import settings
from mcod.resources import guess
from mcod.resources.archives import UnsupportedArchiveError, is_archive_file, ArchiveReader
from mcod.resources.geo import (
    analyze_shapefile,
    are_shapefiles,
    check_geodata,
    is_json_stat_path,
    has_geotiff_files,
)
from mcod.resources.meteo import check_meteo_data
from mcod.unleash import is_enabled

logger = logging.getLogger('mcod')


class UnknownFileFormatError(Exception):
    pass


def _is_office_file(extension, content_type):
    return extension in ('doc', 'docx', 'xls', 'xlsx', 'ods', 'odt') or content_type == 'msword'


def _is_spreadsheet(ext):
    return ext in ('xls', 'xlsx', 'ods')


def _is_plain_text(family, content_type):
    return family == 'text' and content_type == 'plain'


def _isnt_text_encoding(encoding):
    return any((isinstance(encoding, str) and encoding.startswith('unknown'),
                encoding == 'binary',
                not encoding))


def _isnt_msdoc_text(content_type):
    try:
        extensions = next(filter(
            lambda x: x[1] == content_type,
            settings.SUPPORTED_CONTENT_TYPES)
        )[2]
        return len({'doc', 'docx'} & set(extensions)) == 0
    except StopIteration:
        return False


def _analyze_plain_text(path, extension, encoding):
    backup_encoding = 'utf-8'
    if encoding.startswith('unknown') or encoding == 'binary':
        encoding, backup_encoding = guess.file_encoding(path)
        logger.debug(f" encoding (guess-plain): {encoding}")
        logger.debug(f" backup_encoding (guess-plain): {backup_encoding}")

    extension = guess.text_file_format(path, encoding or backup_encoding) or extension
    logger.debug(f"  extension (guess-plain): {extension}")

    return extension, encoding


def _analyze_office_file(path, encoding, content_type, extension):
    tmp_extension = path.rsplit('.')[-1]
    if _isnt_text_encoding(encoding):
        encoding, backup_encoding = guess.file_encoding(path)
        logger.debug(f"  encoding (guess-spreadsheet): {encoding}")
        logger.debug(f"  backup_encoding (guess-spreadsheet): {backup_encoding}")
        encoding = encoding or backup_encoding

    spreadsheet_format = None
    try:
        spreadsheet_format = guess.spreadsheet_file_format(path, encoding)
    except Exception as exc:
        logger.debug(f'guess.spreadsheet_file_format error: {exc}')
    if all((_is_spreadsheet(tmp_extension),
            _isnt_msdoc_text(content_type),
            spreadsheet_format)):
        extension = spreadsheet_format
        logger.debug(f"  extension (guess-spreadsheet): {extension}")
    elif extension == 'zip' and encoding != 'binary':
        extension = tmp_extension

    return extension, encoding


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


def check_support(ext, file_mimetype):
    content_type = file_mimetype.split('/')[-1]
    if _is_office_file(ext, content_type):
        return
    try:
        next(filter(
            lambda x: x[1] == content_type,
            settings.SUPPORTED_CONTENT_TYPES)
        )
        return
    except StopIteration:
        if is_archive_file(content_type):
            raise UnsupportedArchiveError('archives-are-not-supported')

    raise UnknownFileFormatError('unknown-file-format')


def get_file_info(path):
    _magic = magic.Magic(mime=True, mime_encoding=True)
    result = _magic.from_file(path)
    return parse_mime_type(result)


def analyze_file(path, extension=None):  # noqa: C901
    logger.debug(f"analyze_resource_file({path}, {extension})")
    family, content_type, options = get_file_info(path)
    extracted = None
    analyze_exc = None
    if is_archive_file(content_type):
        extracted = ArchiveReader(path)
        if len(extracted) == 1:
            path = extracted[0]
            family, content_type, options = get_file_info(path)
            logger.debug(f"  extracted file {path}")
        else:
            if are_shapefiles(extracted):
                shp_type, options = analyze_shapefile(extracted)
                extension = 'shp'
                content_type = 'shapefile'
                logger.debug(f"  recognized shapefile {shp_type}, {options}")
            elif is_enabled('S29_geotiff_file_support.be') and has_geotiff_files(extracted):
                family = 'image'
                content_type = 'tiff;application=geotiff'

    try:
        content_type, family = check_geodata(path, content_type, family)
    except Exception as exc:
        analyze_exc = Exception(
            [{'code': 'geodata-error', 'message': 'Błąd podczas analizy pliku: {}.'.format(exc.message)}])
    file_info = magic.from_file(path)
    content_type = check_meteo_data(content_type, path, file_info)
    file_mimetype = f'{family}/{content_type}'
    logger.debug(f"  parsed mimetype: {file_mimetype});{options}")
    logger.debug(f"  file info: {file_info}")
    encoding = options.get('charset', 'unknown')
    logger.debug(f"  encoding: {encoding}")

    extension = file_format_from_content_type(content_type, family=family, extension=extension) or path.rsplit('.')[-1]
    logger.debug(f"  extension: {extension}")
    if _is_plain_text(family, content_type):
        extension, encoding = _analyze_plain_text(path, extension, encoding)
    if _is_office_file(extension, content_type):
        extension, encoding = _analyze_office_file(path, encoding, content_type, extension)

    logger.debug(f'  finally: extension = {extension}, file_info = {file_info}, encoding = {encoding}')

    if extension == 'json' and is_enabled('S35_jsonstat.be') and is_json_stat_path(path):
        extension = 'jsonstat'
    if extracted:
        extracted.cleanup()

    return extension, file_info, encoding, path, file_mimetype, analyze_exc
