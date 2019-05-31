# -*- coding: utf-8 -*-

import collections
import datetime
import json
import re
from collections import OrderedDict

import json_api_doc
import jsonschema
from marshmallow.schema import BaseSchema
from marshmallow import class_registry
from marshmallow.utils import UTC

from mcod import settings

_iso8601_datetime_re = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
    r'[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    r'(?P<tzinfo>|[+-]\d{2}(?::?\d{2})?)?$',
)


def flatten_list(l, split_delimeter=None):
    def split(el):
        if split_delimeter and isinstance(el, (str, bytes)):
            el = el.split(split_delimeter)
            return el[0] if len(el) == 1 else el
        return el

    for el in l:
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
            localized = UTC.localize(dt)
        else:
            localized = dt.astimezone(UTC)
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


def route_to_name(route, prefix='api', method='GET'):
    route = '' if not route else route
    route = route.strip('/')
    route = route.strip('$')
    route = route.replace('/', '|')
    if prefix:
        route = '{}|{}'.format(prefix, route)
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
