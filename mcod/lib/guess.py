# -*- coding: utf-8 -*-
import io
import json
import jsonschema
import rdflib
import xml
from chardet import UniversalDetector
from lxml import etree, html
from tabulator import Stream
from tabulator.exceptions import FormatError
from xlrd.biffh import XLRDError
from zipfile import BadZipFile
from mcod import settings

GUESS_FROM_BUFFER = (
    "application/octetstream",
    "application/octet-stream",
    "octet-stream",
    "octetstream",
    "application octet-stream"
)


def is_octetstream(content_type):
    return content_type in GUESS_FROM_BUFFER


def file_encoding(path):
    iso_unique = (b'\xb1', b'\xac', b'\xbc', b'\xa1', b'\xb6', b'\xa6')
    cp_unique = (b'\xb9', b'\xa5', b'\x9f', b'\x8f', b'\x8c', b'\x9c')

    iso_counter = 0
    cp_counter = 0

    _detector = UniversalDetector()
    with open(path, 'rb') as f:
        for line in f.readlines():
            for c in iso_unique:
                iso_counter += line.count(c)
            for c in cp_unique:
                cp_counter += line.count(c)

            _detector.feed(line)
            if _detector.done:
                break
    _detector.close()

    if _detector.result.get('confidence') < 0.95 and (cp_counter or iso_counter):
        return 'Windows-1250' if cp_counter > iso_counter else 'iso-8859-2'
    return _detector.result.get('encoding') or 'utf-8'


def spreadsheet_file_format(path, encoding):  # noqa: C901
    def _xls():
        _s = Stream(path, format='xls', encoding=encoding)
        try:
            _s.open()
            _s.close()
            return 'xls'
        except (FormatError, BadZipFile, ValueError, XLRDError, FileNotFoundError, NotImplementedError):
            return None

    def _xlsx():
        _s = Stream(path, format='xlsx', encoding=encoding)
        try:
            _s.open()
            _s.close()
            return 'xlsx'
        except ValueError:
            return 'xlsx'
        except (FormatError, BadZipFile, OSError, FileNotFoundError, KeyError):
            return None

    def _ods():
        _s = Stream(path, format='ods', encoding=encoding)
        try:
            _s.open()
            _s.close()
            return True

        except (FormatError, OSError, BadZipFile, FileNotFoundError, TypeError):
            return False

    encoding = encoding or 'utf-8'
    for func in (_xls, _xlsx, _ods):
        res = func()
        if res:
            return res

    return None


def _csv(path, encoding):
    _s = Stream(path, format='csv', encoding=encoding)
    try:
        _s.open()
        _s.close()
        return 'csv'
    except (FormatError, UnicodeDecodeError, FileNotFoundError, BadZipFile):
        return None


def _json(source, encoding, content_type='application/json'):
    try:
        if isinstance(source, str):
            with open(source, encoding=encoding) as f:
                json.load(f)
        else:
            source.seek(0)
            json.load(source, encoding=encoding)
        return 'json'
    except (json.decoder.JSONDecodeError, UnicodeDecodeError):
        return None


def _xml(source, encoding):
    try:
        if not isinstance(source, str):
            source.seek(0)
        etree.parse(source, etree.XMLParser())
        return 'xml'
    except etree.XMLSyntaxError:
        return None


def _html(source, encoding):
    try:
        _res = None
        if isinstance(source, str):
            with open(source, 'rb') as fp:
                _res = html.fromstring(fp.read()).find('.//*')
        else:
            source.seek(0)
            _res = html.fromstring(source.read()).find('.//*')

        if _res:
            return 'html'
    except (etree.XMLSyntaxError, IndexError):
        pass

    return None


def _rdf(source, encoding):
    _extension = None
    if isinstance(source, str):
        _extension = source.split('.')[-1]
    else:
        source.seek(0)
    _format = 'xml' if _extension not in ('rdf', 'n3', 'nt', 'trix', 'rdfa', 'xml') else _extension
    try:
        _g = rdflib.Graph()
        _g.parse(source, format=_format)
        return 'rdf'
    except (TypeError, rdflib.exceptions.ParserError, xml.sax._exceptions.SAXParseException):
        return None


def _jsonapi(source, encoding, content_type=None):
    if not isinstance(source, str):
        source.seek(0)
    if _json(source, encoding):
        try:
            with open(settings.JSONAPI_SCHEMA_PATH, 'r') as schemafile:
                schema = json.load(schemafile)

            if isinstance(source, str):
                source_dict = json.load(open(source, 'r'))
            else:
                source.seek(0)
                source_dict = json.load(source)
            jsonschema.validate(source_dict, schema)
            return 'jsonapi'
        except jsonschema.ValidationError:
            pass
    return None


def _openapi(path, encodig, content_type=None):
    # TODO
    pass


def api_format(response, encoding):
    encoding = encoding or 'utf-8'
    source = io.BytesIO(response.content)
    for func in (_jsonapi, _openapi, _json, _xml):
        res = func(source, encoding)  # , response.headers.get('Content-Type')
        if res:
            return res
    return None


def web_format(source, encodig):
    if hasattr(source, 'content'):
        source = io.BytesIO(source.content)
    return _html(source, encodig)


def text_file_format(path, encoding):  # noqa: C901
    encoding = encoding or 'utf-8'
    for func in (_json, _rdf, _html, _xml, _csv):
        res = func(path, encoding)
        if res:
            return res
    return None
