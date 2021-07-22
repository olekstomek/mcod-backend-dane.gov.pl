# -*- coding: utf-8 -*-
import io
import os
import json
import cchardet
from bs4 import BeautifulSoup
import jsonschema
import rdflib
import xml
from chardet import UniversalDetector
from lxml import etree
from tabulator import Stream
from tabulator.exceptions import FormatError, EncodingError
from zipfile import BadZipFile
from mcod import settings
from mcod.unleash import is_enabled


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

    if is_enabled('S18_file_encoding_with_cchardet.be'):
        _detector = cchardet.UniversalDetector()
    else:
        _detector = UniversalDetector()

    with open(path, 'rb') as f:
        for line in f:
            for c in iso_unique:
                iso_counter += line.count(c)
            for c in cp_unique:
                cp_counter += line.count(c)

            _detector.feed(line)
            if _detector.done:
                break
    _detector.close()

    backup_encoding = 'utf-8'
    encoding = _detector.result.get('encoding')
    confidence = _detector.result.get('confidence') or 0.0
    if confidence < 0.95 and (cp_counter or iso_counter):
        backup_encoding = 'Windows-1250' if cp_counter > iso_counter else 'iso-8859-2'
    return encoding, backup_encoding


def spreadsheet_file_format(path, encoding):  # noqa: C901
    encoding = encoding or 'utf-8'
    _s = Stream(path, encoding=encoding)
    _s.open()
    _s.close()
    return _s.format if _s.format != 'inline' else None


def _csv(path, encoding):
    path = os.path.realpath(path.name) if isinstance(path, io.IOBase) else path
    try:
        return spreadsheet_file_format(path, encoding)
    except (FormatError, UnicodeDecodeError, FileNotFoundError, BadZipFile, EncodingError):
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
        if isinstance(source, str):
            source = open(os.path.realpath(source), 'rb')
        if isinstance(source, io.IOBase):
            source.seek(0)
        is_html = bool(BeautifulSoup(source.read(), "html.parser").find('html'))
        return 'html' if is_html else None
    except Exception:
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


def _openapi(path, encoding, content_type=None):
    # TODO
    pass


def api_format(response, encoding):
    encoding = encoding or 'utf-8'
    source = io.BytesIO(response.content)
    for func in (_jsonapi, _openapi, _json, _xml):
        res = func(source, encoding)
        if res:
            return res
    return None


def web_format(source, encoding):
    if hasattr(source, 'content'):
        source = io.BytesIO(source.content)
    return _html(source, encoding)


def text_file_format(path, encoding):  # noqa: C901
    encoding = encoding or 'utf-8'
    for func in (_json, _rdf, _html, _xml, _csv):
        res = func(path, encoding)
        if res:
            return res
    return None
