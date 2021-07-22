import operator

import six
from django.db.models.manager import BaseManager
from django.utils.translation import gettext as _, get_language
from elasticsearch_dsl.query import Q, Bool
from flatdict import FlatDict
from marshmallow import fields
from marshmallow.exceptions import ValidationError
from marshmallow.utils import missing as missing_
from marshmallow.validate import Validator
from marshmallow_jsonapi.fields import Relationship as JSRelationship
from marshmallow_jsonapi.utils import missing, get_value, tpl

from mcod import settings
from mcod.core.api.search import constants
from mcod.lib import field_validators


def resolve_params(obj, params, default=missing):
    """Given a dictionary of keyword arguments, return the same dictionary except with
    values enclosed in `< >` resolved to attributes on `obj`.
    """
    param_values = {}
    for name, attr_tpl in params.items():
        attr_name = tpl(str(attr_tpl))
        if attr_name:
            if attr_name == "slug":
                lang = get_language()
                attribute_value = get_value(obj, f"{attr_name}.{lang}")
                if not attribute_value:
                    attribute_value = get_value(obj, attr_name, default=default)
            else:
                attribute_value = get_value(obj, attr_name, default=default)
            if attribute_value is not missing:
                param_values[name] = attribute_value
            else:
                raise AttributeError(
                    '{attr_name!r} is not a valid '
                    'attribute of {obj!r}'.format(attr_name=attr_name, obj=obj),
                )
        else:
            param_values[name] = attr_tpl
    return param_values


class OldRelationship(JSRelationship):
    def get_value(self, obj, attr, accessor=None, default=missing_):
        _rel = getattr(obj, attr, None)
        if isinstance(_rel, BaseManager):
            return _rel.all()

        return super().get_value(obj, attr, accessor=accessor, default=default)

    def get_related_url(self, obj):
        if self.related_url:
            try:
                params = resolve_params(obj, self.related_url_kwargs, default=self.default)
            except AttributeError:
                return None
            non_null_params = {
                key: value for key, value in params.items()
                if value is not None
            }
            if non_null_params:
                attr = getattr(obj, self.attribute or self.data_key)
                href = self.related_url.format(**non_null_params)
                api_version = self.context.get('api_version')
                href = '/{}{}'.format(api_version, href) if api_version else href
                ret = {'href': href}
                if self.many:
                    count = attr.count() if isinstance(attr, BaseManager) else len(attr)
                    ret['meta'] = {
                        'count': count
                    }
                return ret
        return None


MISSING_ERROR_MESSAGE = (
    'ValidationError raised by `{class_name}`, but error key `{key}` does '
    'not exist in the `error_messages` dictionary.'
)


class TranslatedErrorsMixin(object):
    def make_error(self, key, **kwargs):
        try:
            msg = _(self.error_messages[key])
        except KeyError:
            class_name = self.__class__.__name__
            msg = _(MISSING_ERROR_MESSAGE).format(class_name=class_name, key=key)
            raise AssertionError(msg)
        if isinstance(msg, (str, bytes)):
            msg = msg.format(**kwargs)
        raise ValidationError(msg)

    def _validate(self, value):
        errors = []
        kwargs = {}
        for validator in self.validators:
            try:
                r = validator(value)
                if not isinstance(validator, Validator) and r is False:
                    self.make_error('validator_failed')
            except ValidationError as err:
                kwargs.update(err.kwargs)
                if isinstance(err.messages, dict):
                    errors.append(err.messages)  # TODO
                else:
                    errors.extend((_(msg) for msg in err.messages))
        if errors:
            raise ValidationError(errors, **kwargs)


class DataMixin:
    def prepare_data(self, name, data):
        return data

    def prepare_queryset(self, queryset, context=None):
        return queryset


class SearchFieldMixin:
    @staticmethod
    def _filter_empty(filter_list):
        return list(filter(lambda el: el != '', filter_list))

    def split_lookup_value(self, value, maxsplit=-1):
        return self._filter_empty(value.split(constants.SEPARATOR_LOOKUP_VALUE, maxsplit))

    def split_lookup_filter(self, value, maxsplit=-1):
        return self._filter_empty(value.split(constants.SEPARATOR_LOOKUP_FILTER, maxsplit))

    def split_lookup_complex_value(self, value, maxsplit=-1):
        return self._filter_empty(value.split(constants.SEPARATOR_LOOKUP_COMPLEX_VALUE, maxsplit))


class Raw(DataMixin, TranslatedErrorsMixin, fields.Raw):
    pass


class Nested(DataMixin, TranslatedErrorsMixin, fields.Nested):
    pass


class List(DataMixin, TranslatedErrorsMixin, fields.List):
    pass


class String(DataMixin, TranslatedErrorsMixin, fields.String):
    pass


Str = String


class UUID(DataMixin, TranslatedErrorsMixin, fields.UUID):
    pass


class Number(DataMixin, TranslatedErrorsMixin, fields.Number):
    pass


class Integer(DataMixin, TranslatedErrorsMixin, fields.Integer):
    pass


Int = Integer


class Decimal(DataMixin, TranslatedErrorsMixin, fields.Decimal):
    pass


class Boolean(DataMixin, TranslatedErrorsMixin, fields.Boolean):
    pass


class Float(DataMixin, TranslatedErrorsMixin, fields.Float):
    pass


class DateField(DataMixin, TranslatedErrorsMixin, fields.DateTime):
    pass


class Time(DataMixin, TranslatedErrorsMixin, fields.Time):
    pass


class Date(DataMixin, TranslatedErrorsMixin, fields.Date):
    pass


class TimeDelta(DataMixin, TranslatedErrorsMixin, fields.TimeDelta):
    pass


class Dict(DataMixin, TranslatedErrorsMixin, fields.Dict):
    pass


class Url(DataMixin, TranslatedErrorsMixin, fields.Url):
    pass


class Email(DataMixin, TranslatedErrorsMixin, fields.Email):
    pass


class Method(DataMixin, TranslatedErrorsMixin, fields.Method):
    pass


class Function(DataMixin, TranslatedErrorsMixin, fields.Function):
    pass


class Constant(DataMixin, TranslatedErrorsMixin, fields.Constant):
    pass


class Base64(String):
    default_error_messages = {
        'invalid_base64': 'Invalid data format for base64 encoding.',
        'too_long': 'Too long data.'
    }

    def __init__(self, max_size=None, **kwargs):
        super().__init__(**kwargs)
        self.validators.insert(0, field_validators.Base64(
            max_size=max_size,
            base64_error=self.error_messages['invalid_base64'],
            length_error=self.error_messages['too_long']
        ))


class FilteringFilterField(SearchFieldMixin, DataMixin, TranslatedErrorsMixin, fields.Field):
    def __init__(self, field_name='', lookups=None, translated=False, **metadata):
        super().__init__(**metadata)
        self.lookups = lookups if isinstance(lookups, list) else []
        self.field_name = field_name
        self.trans = translated

    @property
    def _name(self):
        return (self.field_name or self.name) + (f".{get_language()}" if self.trans else "")

    @property
    def _base_name(self):
        return self.field_name or self.name

    def prepare_data(self, name, data):
        data = dict(data)
        if name in data:
            nkey = '%s%s%s' % (name, constants.SEPARATOR_LOOKUP_FILTER, constants.LOOKUP_FILTER_TERM)
            data[nkey] = data.pop(name)
        field_data = {k: v for k, v in data.items() if k.startswith(name)}
        data.update(FlatDict(field_data, delimiter=constants.SEPARATOR_LOOKUP_FILTER).as_dict())
        return data

    def _deserialize(self, value, attr, data):
        if isinstance(value, str):
            return {constants.LOOKUP_FILTER_TERM: value}
        return value

    def _validate(self, values):
        unsupported_lookups = list(set(values.keys() - self.lookups))
        if unsupported_lookups:
            raise ValidationError('Unsupported filter')

    def get_range_params(self, value):
        __values = self.split_lookup_value(value, maxsplit=3)
        __len_values = len(__values)

        if __len_values == 0:
            return {}

        params = {
            'gte': __values[0]
        }

        if __len_values == 3:
            params['lte'] = __values[1]
            params['boost'] = __values[2]
        elif __len_values == 2:
            params['lte'] = __values[1]

        return params

    def get_gte_lte_params(self, value, lookup):
        __values = self.split_lookup_value(value, maxsplit=2)
        __len_values = len(__values)

        if __len_values == 0:
            return {}

        params = {
            lookup: __values[0]
        }

        if __len_values == 2:
            params['boost'] = __values[1]

        return params

    def prepare_queryset(self, queryset, context=None):  # noqa:C901
        data = context or self.context
        if not data:
            return queryset
        if self.trans:
            _qs = []
            for lookup, value in data.items():
                func = getattr(self, 'get_filter_{}'.format(lookup), None)
                if not func:
                    continue
                q = func(value)
                if q:
                    _qs.append(q)

            return queryset.query(Q('nested', path=self._base_name, query=six.moves.reduce(operator.and_, _qs)))
        else:
            for lookup, value in data.items():
                func = getattr(self, 'get_filter_{}'.format(lookup), None)
                if not func:
                    continue
                q = func(value)
                if q:
                    queryset = queryset.query(q)

            return queryset

    def get_filter_onlist(self, value):
        if isinstance(value, (list, tuple)):
            __values = value
        else:
            __values = self.split_lookup_value(value)
        must = []
        for value in list(set(__values)):
            must.append(Q('term', **{self._name: value}))
        return Q('bool', must=must)

    def get_filter_term(self, value):
        return Q('term', **{self._name: value})

    def get_filter_terms(self, value):
        if isinstance(value, (list, tuple)):
            __values = value
        else:
            __values = self.split_lookup_value(value)

        return Q(
            'terms',
            **{self._name: __values}
        )

    def get_filter_range(self, value):
        return Q(
            'range',
            **{self._name: self.get_range_params(value)}
        )

    def get_filter_exists(self, value):
        _value_lower = value.lower()
        if _value_lower in constants.TRUE_VALUES:
            return Q("exists", field=self._name)
        elif _value_lower in constants.FALSE_VALUES:
            return ~Q("exists", field=self._name)
        return None

    def get_filter_prefix(self, value):
        return Q(
            'prefix',
            **{self._name: value}
        )

    def get_filter_wildcard(self, value):
        return Q('wildcard', **{self._name: value})

    def get_filter_contains(self, value):
        return Q('wildcard', **{self._name: '*{}*'.format(value)})

    def get_filter_startswith(self, value):
        return Q('prefix', **{self._name: '{}'.format(value)})

    def get_filter_endswith(self, value):
        return Q('wildcard', **{self._name: '*{}'.format(value)})

    def get_filter_in(self, value):
        return self.get_filter_terms(value)

    def get_filter_gt(self, value):
        return Bool(filter=[
            Q('range', **{self._name: self.get_gte_lte_params(value, 'gt')})
        ])

    def get_filter_gte(self, value):
        return Bool(filter=[
            Q('range', **{self._name: self.get_gte_lte_params(value, 'gte')})
        ])

    def get_filter_lt(self, value):
        return Bool(filter=[Q(
            'range',
            **{self._name: self.get_gte_lte_params(value, 'lt')}
        )])

    def get_filter_lte(self, value):
        return Bool(filter=[Q(
            'range',
            **{self._name: self.get_gte_lte_params(value, 'lte')}
        )])

    def get_filter_exclude(self, value):
        __values = self.split_lookup_value(value)

        __queries = []
        for __value in __values:
            __queries.append(
                ~Q('term', **{self._name: __value})
            )

        if __queries:
            return six.moves.reduce(operator.or_, __queries)

        return None


class NestedFilteringField(FilteringFilterField):
    def __init__(self, path, field_name=None, lookups=[], **kwargs):
        super().__init__(field_name=field_name, lookups=lookups, **kwargs)
        self.path = path

    def prepare_queryset(self, queryset, context=None):  # noqa:C901
        data = context or self.context
        if not data:
            return queryset
        for lookup, value in data.items():
            func = getattr(self, 'get_filter_{}'.format(lookup), None)
            if not func:
                continue
            q = func(value)
            if q:
                queryset = queryset.query('nested', path=self.path, query=q)

        return queryset


class IdsSearchField(SearchFieldMixin, DataMixin, TranslatedErrorsMixin, fields.Field):
    def prepare_queryset(self, queryset, context=None):
        data = context or self.context
        if not data:
            return queryset
        __ids = []
        for item in data:
            __values = self.split_lookup_value(item)
            __ids += __values

        if __ids:
            __ids = list(set(__ids))
            queryset = queryset.query(
                'ids', **{'values': __ids}
            )
        return queryset


class SuggesterFilterField(SearchFieldMixin, DataMixin, TranslatedErrorsMixin, fields.Field):
    def __init__(self, field, suggesters=None, **metadata):
        self.field_name = field
        self.suggesters = suggesters if isinstance(suggesters, list) else (constants.ALL_SUGGESTERS,)
        super().__init__(**metadata)

    def prepare_data(self, name, data):
        data = dict(data)
        field_data = {k: v for k, v in data.items() if k.startswith(name)}
        data.update(FlatDict(field_data, delimiter=constants.SEPARATOR_LOOKUP_FILTER).as_dict())
        return data

    def apply_suggester_term(self, queryset, value):
        return queryset.suggest(
            self.name,
            value,
            term={'field': self.field_name}
        )

    def apply_suggester_phrase(self, queryset, value):
        return queryset.suggest(
            self.name,
            value,
            phrase={'field': self.field_name}
        )

    def apply_suggester_completion(self, queryset, value):
        return queryset.suggest(
            self.name,
            value,
            completion={'field': self.field_name}
        )

    def prepare_queryset(self, queryset, context=None):
        data = context or self.context
        if not data:
            return queryset
        for suggester_type, value in data.items():
            if suggester_type in self.suggesters:
                if suggester_type == constants.SUGGESTER_TERM:
                    queryset = self.apply_suggester_term(queryset, value)
                elif suggester_type == constants.SUGGESTER_PHRASE:
                    queryset = self.apply_suggester_phrase(queryset, value)
                elif suggester_type == constants.SUGGESTER_COMPLETION:
                    queryset = self.apply_suggester_completion(queryset, value)
        return queryset


class SearchFilterField(SearchFieldMixin, DataMixin, TranslatedErrorsMixin, fields.Field):
    def __init__(self, search_fields=None, search_nested_fields=None, search_i18n_fields=None, **metadata):
        self.field_names = search_fields if isinstance(search_fields, (list, tuple, dict)) else ()
        self.search_nested_fields = search_nested_fields if isinstance(search_nested_fields, dict) else {}
        self.search_i18n_fields = search_i18n_fields if isinstance(search_i18n_fields, (list, tuple)) else ()
        super().__init__(**metadata)

    def _deserialize(self, value, attr, data):
        if isinstance(value, str):
            return [value, ]
        return value

    def construct_nested_search(self, data):
        __queries = []
        for search_term in data:
            for path, _fields in self.search_nested_fields.items():
                queries = []
                for field in _fields:
                    field_key = "{}.{}".format(path, field)
                    queries.append(
                        Q("match", **{field_key: {
                            'query': search_term,
                            'fuzziness': 'AUTO',
                            'fuzzy_transpositions': True
                        }})
                    )

                __queries.append(
                    Q(
                        "nested",
                        path=path,
                        query=six.moves.reduce(operator.or_, queries)
                    )
                )

        return __queries

    def construct_translated_search(self, data):
        __queries = []
        for search_term in data:
            for field in self.search_i18n_fields:
                queries = []
                for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES:
                    field_key = f"{field}.{lang}"
                    queries += [
                        Q("match", **{field_key: {
                            'query': search_term,
                            'fuzziness': 'AUTO',
                            'fuzzy_transpositions': True
                        }}),
                        Q("match", **{field_key + ".asciied": {
                            'query': search_term,
                            'fuzziness': 'AUTO',
                            'fuzzy_transpositions': True
                        }}),
                    ]

                __queries.append(
                    Q(
                        "nested",
                        path=field,
                        query=six.moves.reduce(operator.or_, queries)
                    )
                )
        return __queries

    def _prepare_match_query(self, field, value):
        # Initial kwargs for the match query
        field_kwargs = {field: {
            'query': value,
            'fuzziness': 'AUTO',
            'fuzzy_transpositions': True,
        }}
        # In case if we deal with structure 2
        if isinstance(self.field_names, dict):
            extra_field_kwargs = self.field_names[field]
            if extra_field_kwargs:
                field_kwargs[field].update(extra_field_kwargs)

        return Q("match", **field_kwargs)

    def construct_search(self, data):
        __queries = []

        for search_term in data:
            __values = self.split_lookup_value(search_term, 1)
            __len_values = len(__values)
            if __len_values > 1:
                field, value = __values
                if field in self.field_names:
                    __queries.append(
                        self._prepare_match_query(field, value)
                    )

            else:
                for field in self.field_names:
                    __queries.append(
                        self._prepare_match_query(field, search_term)
                    )
        return __queries

    def prepare_queryset(self, queryset, context=None):
        data = context or self.context
        if not data:
            return queryset
        __queries = sum((self.construct_search(data),
                         self.construct_nested_search(data),
                         self.construct_translated_search(data)),
                        [])

        if __queries:
            queryset = queryset.query('bool', should=__queries)
        return queryset


class FacetedFilterField(SearchFieldMixin, DataMixin, TranslatedErrorsMixin, fields.Field):
    def __init__(self, facets=None, **metadata):
        self.facets = facets if isinstance(facets, dict) else {}
        super().__init__(**metadata)

    def _deserialize(self, value, attr, data):
        if isinstance(value, str):
            return value.split(',')
        return value

    def prepare_queryset(self, queryset, context=None):
        data = context or self.context
        if not data:
            return queryset

        for __field, __facet in self.facets.items():
            if __field in data:
                agg = __facet.get_aggregation()
                agg_filter = Q('match_all')

                queryset.aggs.bucket(
                    '_filter_' + __field,
                    'filter',
                    filter=agg_filter
                ).bucket(__field, agg)
        return queryset


class GeoSpatialFilteringFilterField(SearchFieldMixin, DataMixin, TranslatedErrorsMixin, fields.Field):
    pass


class GeoSpatialOrderingFilterField(SearchFieldMixin, DataMixin, TranslatedErrorsMixin, fields.Field):
    pass


class OrderingFilterField(SearchFieldMixin, DataMixin, TranslatedErrorsMixin, fields.Field):
    ordering_param = 'sort'

    def __init__(self, ordering_fields=None, default_ordering=None, **metadata):
        self.ordering_fields = ordering_fields if isinstance(ordering_fields, dict) else {}
        self.ordering_fields['_score'] = '_score'
        self.default_ordering = default_ordering or []
        super().__init__(**metadata)

    def prepare_fields_data(self, data):
        sort_params = data or self.default_ordering
        if isinstance(sort_params, str):
            sort_params = [sort_params, ]
        __sort_params = []
        for param in sort_params:
            __key = param.lstrip('-')
            __direction = '-' if param.startswith('-') else ''
            if __key in self.ordering_fields:
                __field_name = self.ordering_fields[__key] or __key
                if '{lang}' in __field_name:
                    __field_name = __field_name.format(lang=get_language())
                    nested_path = __field_name.split('.')[0]
                    __sort_params.append({
                        __field_name: {
                            'order': 'desc' if __direction == '-' else 'asc',
                            'nested': {
                                'path': nested_path
                            }
                        }
                    })
                else:
                    __sort_params.append('{}{}'.format(__direction, __field_name.format(lang=get_language())))
        return __sort_params

    def prepare_queryset(self, queryset, context=None):
        data = context or self.context
        if not data:
            return queryset

        return queryset.sort(*self.prepare_fields_data(data))


class HighlightBackend(SearchFieldMixin, DataMixin, TranslatedErrorsMixin, fields.Field):
    _ALL = '_all'
    _ES_ALL_KEY = _ALL

    def __init__(self, highlight_fields=None, **metadata):
        self.highlight_fields = highlight_fields or {}
        super().__init__(**metadata)

    def prepare_fields_data(self, data):
        highlight_fields = data or []
        __params = {}
        if isinstance(highlight_fields, str):
            highlight_fields = [highlight_fields, ]

        if self._ALL in self.highlight_fields:
            __params[self._ES_ALL_KEY] = self.highlight_fields[self._ALL]
            __params[self._ES_ALL_KEY]['enabled'] = True

        for field in highlight_fields:
            if field in self.highlight_fields:
                if 'enabled' not in self.highlight_fields[field]:
                    self.highlight_fields[field]['enabled'] = False

                if 'options' not in self.highlight_fields[field]:
                    self.highlight_fields[field]['options'] = {}
                __params[field] = self.highlight_fields[field]
        return __params

    def prepare_queryset(self, queryset, context=None):
        data = context or self.context
        if not data:
            return queryset

        params = self.prepare_fields_data(data)

        for __field, __options in params.items():
            if __options['enabled']:
                queryset = queryset.highlight(__field, **__options['options'])

        return queryset

#
# class GeoSpatialFilteringFilterBackend(BaseFilterBackend, FilterBackendMixin):
#     @classmethod
#     def prepare_filter_fields(cls, resource):
#         filter_fields = getattr(resource, 'geo_spatial_filter_fields', {})
#
#         for field, options in filter_fields.items():
#             if options is None or isinstance(options, six.string_types):
#                 filter_fields[field] = {
#                     'field': options or field
#                 }
#             elif 'field' not in filter_fields[field]:
#                 filter_fields[field]['field'] = field
#
#             if 'lookups' not in filter_fields[field]:
#                 filter_fields[field]['lookups'] = tuple(
#                     constants.ALL_GEO_SPATIAL_LOOKUP_FILTERS_AND_QUERIES
#                 )
#
#         return filter_fields
#
#     @classmethod
#     def get_geo_distance_params(cls, value, field):
#         __values = cls.split_lookup_value(value, maxsplit=3)
#         __len_values = len(__values)
#
#         if __len_values < 3:
#             return {}
#
#         params = {
#             'distance': __values[0],
#             field: {
#                 'lat': __values[1],
#                 'lon': __values[2],
#             }
#         }
#
#         if __len_values == 4:
#             params['distance_type'] = __values[3]
#         else:
#             params['distance_type'] = 'sloppy_arc'
#
#         return params
#
#     @classmethod
#     def get_geo_polygon_params(cls, value, field):
#         __values = cls.split_lookup_value(value)
#         __len_values = len(__values)
#
#         if not __len_values:
#             return {}
#
#         __points = []
#         __options = {}
#
#         for __value in __values:
#             if constants.SEPARATOR_LOOKUP_COMPLEX_MULTIPLE_VALUE in __value:
#                 __lat_lon = __value.split(
#                     constants.SEPARATOR_LOOKUP_COMPLEX_MULTIPLE_VALUE
#                 )
#                 if len(__lat_lon) >= 2:
#                     __points.append(
#                         {
#                             'lat': float(__lat_lon[0]),
#                             'lon': float(__lat_lon[1]),
#                         }
#                     )
#
#             elif constants.SEPARATOR_LOOKUP_COMPLEX_VALUE in __value:
#                 __opt_name_val = __value.split(
#                     constants.SEPARATOR_LOOKUP_COMPLEX_VALUE
#                 )
#                 if len(__opt_name_val) >= 2:
#                     if __opt_name_val[0] in ('_name', 'validation_method'):
#                         __options.update(
#                             {
#                                 __opt_name_val[0]: __opt_name_val[1]
#                             }
#                         )
#
#         if __points:
#             params = {
#                 field: {
#                     'points': __points
#                 }
#             }
#             params.update(__options)
#
#             return params
#         return {}
#
#     @classmethod
#     def get_geo_bounding_box_params(cls, value, field):
#         __values = cls.split_lookup_value(value)
#         __len_values = len(__values)
#
#         if not __len_values:
#             return {}
#
#         __top_left_points = {}
#         __bottom_right_points = {}
#         __options = {}
#
#         # Top left
#         __lat_lon = __values[0].split(
#             constants.SEPARATOR_LOOKUP_COMPLEX_MULTIPLE_VALUE
#         )
#         if len(__lat_lon) >= 2:
#             __top_left_points.update({
#                 'lat': float(__lat_lon[0]),
#                 'lon': float(__lat_lon[1]),
#             })
#
#         # Bottom right
#         __lat_lon = __values[1].split(
#             constants.SEPARATOR_LOOKUP_COMPLEX_MULTIPLE_VALUE
#         )
#         if len(__lat_lon) >= 2:
#             __bottom_right_points.update({
#                 'lat': float(__lat_lon[0]),
#                 'lon': float(__lat_lon[1]),
#             })
#
#         # Options
#         for __value in __values[2:]:
#             if constants.SEPARATOR_LOOKUP_COMPLEX_VALUE in __value:
#                 __opt_name_val = __value.split(
#                     constants.SEPARATOR_LOOKUP_COMPLEX_VALUE
#                 )
#                 if len(__opt_name_val) >= 2:
#                     if __opt_name_val[0] in ('_name',
#                                              'validation_method',
#                                              'type'):
#                         __options.update(
#                             {
#                                 __opt_name_val[0]: __opt_name_val[1]
#                             }
#                         )
#
#         if not __top_left_points or not __bottom_right_points:
#             return {}
#
#         params = {
#             field: {
#                 'top_left': __top_left_points,
#                 'bottom_right': __bottom_right_points,
#             }
#         }
#         params.update(__options)
#
#         return params
#
#     @classmethod
#     def apply_query_geo_distance(cls, queryset, options, value):
#         return queryset.query(
#             Q(
#                 'geo_distance',
#                 **cls.get_geo_distance_params(value, options['field'])
#             )
#         )
#
#     @classmethod
#     def apply_query_geo_polygon(cls, queryset, options, value):
#         return queryset.query(
#             Q(
#                 'geo_polygon',
#                 **cls.get_geo_polygon_params(value, options['field'])
#             )
#         )
#
#     @classmethod
#     def apply_query_geo_bounding_box(cls, queryset, options, value):
#         return queryset.query(
#             Q(
#                 'geo_bounding_box',
#                 **cls.get_geo_bounding_box_params(value, options['field'])
#             )
#         )
#
#     def get_filter_query_params(self, resource, params):
#
#         query_params = params.copy()
#
#         filter_query_params = {}
#         filter_fields = self.prepare_filter_fields(resource)
#         for query_param in query_params:
#             query_param_list = self.split_lookup_filter(
#                 query_param,
#                 maxsplit=1
#             )
#             field_name = query_param_list[0]
#
#             if field_name in filter_fields:
#                 lookup_param = None
#                 if len(query_param_list) > 1:
#                     lookup_param = query_param_list[1]
#
#                 valid_lookups = filter_fields[field_name]['lookups']
#
#                 if lookup_param is None or lookup_param in valid_lookups:
#                     values = [
#                         __value.strip()
#                         for __value
#                         in query_params.getlist(query_param)
#                         if __value.strip() != ''
#                     ]
#
#                     if values:
#                         filter_query_params[query_param] = {
#                             'lookup': lookup_param,
#                             'values': values,
#                             'field': filter_fields[field_name].get(
#                                 'field',
#                                 field_name
#                             ),
#                             'type': resource.mapping
#                         }
#         return filter_query_params
#
#     def filter_queryset(self, resource, queryset, params):
#         filter_query_params = self.get_filter_query_params(resource, params)
#         for options in filter_query_params.values():
#
#             # For all other cases, when we don't have multiple values,
#             # we follow the normal flow.
#             for value in options['values']:
#
#                 # `geo_distance` query lookup
#                 if options['lookup'] == constants.LOOKUP_FILTER_GEO_DISTANCE:
#                     queryset = self.apply_query_geo_distance(
#                         queryset,
#                         options,
#                         value
#                     )
#
#                 # `geo_polygon` query lookup
#                 elif options['lookup'] == constants.LOOKUP_FILTER_GEO_POLYGON:
#                     queryset = self.apply_query_geo_polygon(
#                         queryset,
#                         options,
#                         value
#                     )
#
#                 # `geo_bounding_box` query lookup
#                 elif options['lookup'] == constants.LOOKUP_FILTER_GEO_BOUNDING_BOX:
#                     queryset = self.apply_query_geo_bounding_box(
#                         queryset,
#                         options,
#                         value
#                     )
#
#         return queryset
#
#
# class GeoSpatialOrderingFilterBackend(BaseFilterBackend, FilterBackendMixin):
#     ordering_param = constants.GEO_DISTANCE_ORDERING_PARAM
#
#     @classmethod
#     def get_geo_distance_params(cls, value, field):
#         __values = cls.split_lookup_value(value, maxsplit=3)
#         __len_values = len(__values)
#
#         if __len_values < 2:
#             return {}
#
#         params = {
#             field: {
#                 'lat': __values[0],
#                 'lon': __values[1],
#             }
#         }
#
#         if __len_values > 2:
#             params['unit'] = __values[2]
#         else:
#             params['unit'] = 'm'
#         if __len_values > 3:
#             params['distance_type'] = __values[3]
#         else:
#             params['distance_type'] = 'sloppy_arc'
#
#         return params
#
#     def get_ordering_query_params(self, resource, params):
#         query_params = params.copy()
#         ordering_query_params = query_params.get(self.ordering_param, [])
#         __ordering_params = []
#         # Remove invalid ordering query params
#         for query_param in ordering_query_params:
#             __key, __value = FilterBackendMixin.split_lookup_value(
#                 query_param.lstrip('-'),
#                 maxsplit=1,
#             )
#             __direction = 'desc' if query_param.startswith('-') else 'asc'
#             if __key in resource.geo_spatial_ordering_fields:
#                 __field_name = resource.geo_spatial_ordering_fields[__key] or __key
#                 __params = self.get_geo_distance_params(__value, __field_name)
#                 __params['order'] = __direction
#                 __ordering_params.append(__params)
#
#         return __ordering_params
#
#     def filter_queryset(self, resource, queryset, params):
#         ordering_query_params = self.get_ordering_query_params(resource, params)
#
#         if ordering_query_params:
#             return queryset.sort(*ordering_query_params)
#
#         return queryset
