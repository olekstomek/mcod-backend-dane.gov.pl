import logging

import magic
from mimeparse import parse_mime_type

from mcod import settings
from mcod.resources import guess
from mcod.resources.archives import (
    ArchiveReader,
    UnsupportedArchiveError,
    is_archive_file,
    is_password_protected_archive_file,
)
from mcod.resources.geo import analyze_shapefile, are_shapefiles, check_geodata, has_geotiff_files
from mcod.resources.meteo import check_meteo_data

logger = logging.getLogger('mcod')


class UnknownFileFormatError(Exception):
    pass


class PasswordProtectedArchiveError(Exception):
    pass


def _is_json(family, content_type):
    return family == 'application' and content_type == 'json'


def _is_xml(family, content_type):
    return family == 'text' and content_type == 'xml'


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
    items = settings.CONTENT_TYPE_TO_EXTENSION_MAP
    results = list(filter(
        lambda x: x[0] == family and x[1] == content_type if family else x[1] == content_type, items))

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


def analyze_file(path):  # noqa: C901
    logger.debug(f"analyze_resource_file({path})")
    family, content_type, options = get_file_info(path)
    extracted = None
    extracted_extension = None
    extracted_mimetype = None
    extracted_encoding = None
    is_password_protected_archive = False
    if is_archive_file(content_type):
        with open(path, 'rb') as file:
            if is_password_protected_archive_file(file):
                logger.debug(f"  password protected file {path}")
                is_password_protected_archive = True

        if not is_password_protected_archive:
            extracted = ArchiveReader(path)
            if len(extracted) == 1:
                extracted_path = extracted[0]
                extracted_family, extracted_content_type, extracted_options = get_file_info(extracted_path)
                logger.debug(f"  extracted file {extracted_path}")
                extracted_extension, _, extracted_encoding, _, extracted_mimetype, _ = evaluate_file_details(
                    extracted_content_type, extracted_family, extracted_options, extracted_path, bool(extracted)
                )
                logger.debug(f'  extracted extension: {extracted_extension}')
                logger.debug(f'  extracted mimetype: {extracted_mimetype}')
            else:
                if are_shapefiles(extracted):
                    shp_type, options = analyze_shapefile(extracted)
                    content_type = 'shapefile'
                elif has_geotiff_files(extracted):
                    family = 'image'
                    content_type = 'tiff;application=geotiff'

    extension, file_info, encoding, path, file_mimetype, analyze_exc = evaluate_file_details(
        content_type, family, options, path, bool(extracted)
    )

    if is_password_protected_archive and not analyze_exc:
        analyze_exc = PasswordProtectedArchiveError()

    logger.debug(f'  finally: extension = {extension}, file_info = {file_info}, encoding = {encoding}')

    if extracted:
        extracted.cleanup()

    return extension, file_info, encoding, path, file_mimetype, analyze_exc, \
        extracted_extension, extracted_mimetype, extracted_encoding


def evaluate_file_details(content_type, family, options, path, is_extracted):
    analyze_exc = None
    try:
        content_type, family = check_geodata(path, content_type, family, is_extracted=is_extracted)
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

    extension = file_format_from_content_type(content_type, family=family) or path.rsplit('.')[-1]

    logger.debug(f"  extension: {extension}")

    if _is_plain_text(family, content_type) or _is_json(family, content_type) or _is_xml(family, content_type):
        extension, encoding = _analyze_plain_text(path, extension, encoding)

    if _is_office_file(extension, content_type):
        extension, encoding = _analyze_office_file(path, encoding, content_type, extension)
    return extension, file_info, encoding, path, file_mimetype, analyze_exc
