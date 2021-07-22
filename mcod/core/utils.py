# -*- coding: utf-8 -*-

import collections
import csv
import datetime
import json
import re
from collections import OrderedDict
from http.cookies import SimpleCookie
from typing import Union
from pytz import utc

import json_api_doc
import jsonschema
from django.utils.translation import activate
from falcon import Response
from marshmallow import class_registry
from marshmallow.schema import BaseSchema
from mcod import settings

_iso8601_datetime_re = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
    r'[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    r'(?P<tzinfo>|[+-]\d{2}(?::?\d{2})?)?$',
)


def flatten_list(list_, split_delimeter=None):
    def split(el):
        if split_delimeter and isinstance(el, (str, bytes)):
            el = el.split(split_delimeter)
            return el[0] if len(el) == 1 else el
        return el

    for el in list_:
        el = split(el)

        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten_list(el)
        else:
            yield el


def jsonapi_validator(data):
    with open(settings.JSONAPI_SCHEMA_PATH, 'r') as schemafile:
        schema = json.load(schemafile)

    try:
        jsonschema.validate(data, schema)
        validated = json_api_doc.parse(data)
        return True, validated, []
    except (jsonschema.ValidationError, AttributeError) as e:
        errors = [t.message for t in e.context]
        return False, None, errors


def isoformat_with_z(dt, localtime=False, *args, **kwargs):
    """Return the ISO8601-formatted UTC representation of a datetime object."""
    if localtime and dt.tzinfo is not None:
        localized = dt
    else:
        if dt.tzinfo is None:
            localized = utc.localize(dt)
        else:
            localized = dt.astimezone(utc)
    return localized.strftime('%Y-%m-%dT%H:%M:%SZ')


def from_iso_with_z_datetime(datetimestring):
    if not _iso8601_datetime_re.match(datetimestring):
        raise ValueError('Not a valid ISO8601-formatted datetime string')

    return datetime.datetime.strptime(datetimestring[:19], '%Y-%m-%dT%H:%M:%SZ')


def resolve_schema_cls(schema):
    """
    """
    if isinstance(schema, type) and issubclass(schema, BaseSchema):
        return schema
    if isinstance(schema, BaseSchema):
        return type(schema)
    return class_registry.get_class(schema)


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def route_to_name(route, method='GET'):
    route = '' if not route else route
    route = route.strip('$')
    method = method or 'GET'
    return '{} {}'.format(method, route)


def order_dict(d):
    return {k: order_dict(v) if isinstance(v, dict) else v
            for k, v in sorted(d.items())}


class frozendict(collections.Mapping):
    dict_cls = dict

    def __init__(self, *args, **kwargs):
        self._dict = self.dict_cls(*args, **kwargs)
        self._hash = None

    def __getitem__(self, key):
        return self._dict[key]

    def __contains__(self, key):
        return key in self._dict

    def copy(self, **add_or_replace):
        return self.__class__(self, **add_or_replace)

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self._dict)

    def __hash__(self):
        if self._hash is None:
            h = 0
            for key, value in self._dict.items():
                h ^= hash((key, value))
            self._hash = h
        return self._hash


class FrozenOrderedDict(frozendict):
    dict_cls = OrderedDict


class hashabledict(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))


def setpathattr(obj, path, value):
    """
    Sets object subattribute given by path
    Similar to setattr but with path supported.
    eg: setpathattr(data, 'hits.notes.pl', 'polski opis')
    """
    path = path.split('.')
    for step in path[:-1]:
        obj = getattr(obj, step)
    setattr(obj, path[-1], value)


def falcon_set_cookie(
    response: Response,
    name: str,
    value: str,
    same_site: Union[None, str] = '',
    path: str = None,
    secure: bool = True,
    http_only: bool = False,
    domain: str = settings.SESSION_COOKIE_DOMAIN
):
    cookie = SimpleCookie()
    cookie[name] = value
    if same_site is None or same_site:
        cookie[name]['samesite'] = str(same_site)

    if path:
        cookie[name]['path'] = path

    cookie[name]['secure'] = secure
    cookie[name]['httponly'] = http_only
    cookie[name]['domain'] = domain

    response.append_header('Set-Cookie', cookie[name].output(header=''))


def lazy_proxy_to_es_translated_field(lazy_proxy):
    translations = {}
    for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
        activate(lang)
        translations[lang] = str(lazy_proxy)
    return translations


class XmlTagIterator:
    def __init__(self, iterator, close_tags=False):
        self.iterator = iterator
        self.iter = None
        self.tag = None
        self.phrase = None
        self.pos = None
        self.cut = 2 if close_tags else 1
        self.move_forward()

    def move_forward(self):
        try:
            self.iter = next(self.iterator)
            self.tag = self.iter.string[self.iter.span()[0] + self.cut:self.iter.span()[1] - 1]
            self.pos = self.iter.span()[0]
        except StopIteration:
            self.pos = float('inf')
            self.tag = None
            raise

    def __lt__(self, other):
        return self.pos < other.pos

    def __eq__(self, other):
        if isinstance(other, XmlTagIterator):
            return self.tag == other.tag
        return False


def complete_invalid_xml(phrase):
    open_re = re.compile(r'<\w+>')
    close_re = re.compile(r'</\w+>')

    open_tag = XmlTagIterator(open_re.finditer(phrase))
    close_tag = XmlTagIterator(close_re.finditer(phrase), True)

    openings_missing = []
    opened_tags = []

    while True:
        try:
            if close_tag < open_tag:
                if opened_tags and opened_tags[-1] == close_tag.tag:
                    opened_tags.pop()
                else:
                    openings_missing.append(close_tag.tag)
                close_tag.move_forward()
            else:
                if close_tag == open_tag:
                    close_tag.move_forward()
                else:
                    opened_tags.append(open_tag.tag)
                open_tag.move_forward()
        except StopIteration:
            if open_tag.tag is None and close_tag.tag is None:
                break

    return ''.join((
        ''.join('<{}>'.format(tag) for tag in openings_missing[::-1]),
        phrase,
        ''.join('</{}>'.format(tag) for tag in opened_tags[::-1])
    ))


def save_as_csv(file_object, headers, data, delimiter=';'):
    csv_writer = csv.DictWriter(file_object, fieldnames=headers, delimiter=delimiter)
    csv_writer.writeheader()
    for row in data:
        csv_writer.writerow(row)
