import collections
import functools
import operator
import re
from functools import reduce

from django.utils.translation import get_language
from elasticsearch_dsl import Field as DSLField, Q
from elasticsearch_dsl import TermsFacet
from elasticsearch_dsl.query import Bool
from marshmallow import class_registry, utils
from marshmallow.base import SchemaABC

from mcod.core.api import fields
from mcod.core.api.search.facets import NestedFacet
from mcod.core.utils import flatten_list

TRUE_VALUES = ('true', 'yes', 'on', '"true"', '1', '"on"', '"yes"')
FALSE_VALUES = (
    'false', '"false"', 'no', 'off', '"off"', '"no"', '"0"', '""', '', '0', '0.0',
)


class AliasField(DSLField):
    name = 'alias'


class ICUSortField(DSLField):
    name = 'icu_collation_keyword'


class ElasicField(object):
    @property
    def _name(self):
        return getattr(self, 'data_key') or getattr(self, 'name')

    @property
    def _context(self):
        return getattr(self, 'context', {})

    @property
    def nested_search(self):
        return self._context.get('nested_search', False)

    @property
    def search_path(self):
        return self._context.get('search_path', None)

    @property
    def query_field_name(self):
        s = self._context.get('query_field', self._name)
        return s

    def q(self, value):
        raise NotImplementedError

    @fields.after_serialize
    def to_es(self, value):
        if isinstance(value, (collections.Iterable, str, bytes)):
            value = None if not value else value

        if value is not None:
            value = self.q(value)

        return self._prepare_queryset, value

    def _prepare_queryset(self, queryset, data):
        if not data:
            return queryset
        return queryset.query('nested', path=self.search_path, query=data) \
            if self.nested_search else queryset.query(data)


class RangeLtField(ElasicField, fields.String):
    def q(self, value):
        return Bool(filter=[Q(
            'range',
            **{self.query_field_name: {'lt': value}}
        )])


class RangeGtField(ElasicField, fields.String):
    def q(self, value):
        return Bool(filter=[Q(
            'range',
            **{self.query_field_name: {'gt': value}}
        )])


class RangeLteField(ElasicField, fields.String):
    def q(self, value):
        return Bool(filter=[Q(
            'range',
            **{self.query_field_name: {'lte': value}}
        )])


class RangeGteField(ElasicField, fields.String):
    def q(self, value):
        return Bool(filter=[Q(
            'range',
            **{self.query_field_name: {'gte': value}}
        )])


class WildcardField(ElasicField, fields.String):
    @property
    def wildcard(self):
        return self.metadata.get('wildcard', '*{}*')

    def q(self, value):
        return Q('wildcard', **{self.query_field_name: self.wildcard.format(value)})


class PrefixField(ElasicField, fields.String):
    def q(self, value):
        return Q('prefix', **{self.query_field_name: '{}'.format(value)})


class TermField(ElasicField, fields.String):
    def q(self, value):
        return Q('term', **{self.query_field_name: value})


class TermsField(ElasicField, fields.List):
    def __init__(self, cls_or_instance=fields.String, **kwargs):
        super().__init__(cls_or_instance, **kwargs)

    @fields.before_deserialize
    def prepare_value(self, value=None, attr=None, data=None):
        if not isinstance(value, collections.Iterable) or isinstance(value, (str, bytes)):
            value = [value, ]

        value = flatten_list(value, split_delimeter=',')
        value = list(filter(None, value))
        return value, attr, data

    def q(self, value):
        if isinstance(value, (list, tuple)):
            __values = value
        else:
            __values = list(value)

        return Q(
            'terms',
            **{self.query_field_name: __values}
        )


class ExistsField(ElasicField, fields.String):
    def q(self, value):
        _value_lower = value.lower()
        if _value_lower in TRUE_VALUES:
            return Q("exists", field=self.query_field_name)
        elif _value_lower in FALSE_VALUES:
            return ~Q("exists", field=self.query_field_name)
        return ()


class ExcludeField(ElasicField, fields.List):
    def __init__(self, cls_or_instance=fields.String, **kwargs):
        super().__init__(cls_or_instance, **kwargs)

    @fields.before_deserialize
    def prepare_value(self, value=None, attr=None, data=None):
        if not isinstance(value, collections.Iterable) or isinstance(value, (str, bytes)):
            value = [value, ]

        value = flatten_list(value, split_delimeter=',')
        return value, attr, data

    def q(self, values):
        if isinstance(values, (list, tuple)):
            __values = values
        else:
            __values = list(values)

        queries = []
        for value in __values:
            queries.append(
                ~Q('term', **{self.query_field_name: value})
            )

        if queries:
            return reduce(operator.or_, queries)

        return None


class FacetField(ElasicField, fields.Nested):
    def __init__(self, nested, default=utils.missing, exclude=tuple(), only=None, **kwargs):
        super().__init__(nested, default=default, exclude=exclude, only=only, **kwargs)
        self._metadata['explode'] = self._metadata.get('explode', True)
        self._metadata['style'] = self._metadata.get('style', 'deepObject')
        self._metadata['_in'] = self._metadata.get('_in', 'query')

    def q(self, value):
        return list(value.values())

    def _prepare_queryset(self, queryset, data):
        for f, d in data:
            queryset = f(queryset, d)
        return queryset


class FilterField(ElasicField, fields.Nested):
    def __init__(self, nested, default=utils.missing, exclude=tuple(), only=None, **kwargs):
        self.__schema = None
        super().__init__(nested, default=default, exclude=exclude, only=only, **kwargs)
        self._metadata['explode'] = self._metadata.get('explode', True)
        self._metadata['style'] = self._metadata.get('style', 'deepObject')
        self._metadata['_in'] = self._metadata.get('_in', 'query')
        #
        # self._schema.context = getattr(self._schema, 'context') or {}
        # self._schema.context.update(self.extra_context)

    @fields.before_deserialize
    def before_deserialize(self, value=None, attr=None, data=None):
        if not isinstance(value, dict):
            _meta = getattr(self.schema, 'Meta')
            if _meta and hasattr(_meta, 'default_field'):
                value = {
                    _meta.default_field: value
                }
            data[attr] = value
        return value, attr, data

    @property
    def extra_context(self):
        translated = self._metadata.get('translated', False)
        query_field = self._metadata.get('query_field', self._name)
        lang = get_language()
        context = {
            'query_field': query_field,
            'search_path': self._metadata.get('search_path', None),
            'nested_search': self._metadata.get('nested_search', False)
        }

        if translated:
            context['nested_search'] = True
            context['query_field'] = context['query_field'] + "." + lang

        return context

    @property
    def schema(self):
        if not self.__schema:
            # Inherit context from parent.
            if isinstance(self.nested, SchemaABC):
                self.__schema = self.nested
                self.__schema.context = getattr(self.__schema, 'context') or {}
                self.__schema.context.update(self.extra_context)
            else:
                if isinstance(self.nested, type) and issubclass(self.nested, SchemaABC):
                    schema_class = self.nested
                elif not isinstance(self.nested, (str, bytes)):
                    raise ValueError(
                        'Nested fields must be passed a '
                        'Schema, not {0}.'.format(self.nested.__class__),
                    )
                elif self.nested == 'self':
                    schema_class = self.parent.__class__
                else:
                    schema_class = class_registry.get_class(self.nested)
                self.__schema = schema_class(
                    many=self.many,
                    only=self.only, exclude=self.exclude, context=self.extra_context,
                    load_only=self._nested_normalized_option('load_only'),
                    dump_only=self._nested_normalized_option('dump_only'),
                )
            self.__schema.ordered = getattr(self.parent, 'ordered', False)
        return self.__schema

    def q(self, value):
        return list(value.values())

    def _prepare_queryset(self, queryset, data):
        for f, d in data:
            queryset = f(queryset, d)
        return queryset


class MatchPhrasePrefixField(ElasicField, fields.String):
    def q(self, value):
        return Q('match_phrase_prefix', **{self.query_field_name: value})


class MatchPhraseField(ElasicField, fields.String):
    def q(self, value):
        return Q('match_phrase', **{self.query_field_name: value})


class MatchField(ElasicField, fields.String):
    def q(self, value):
        return Q('match', **{self.query_field_name: {
            'query': value,
            'fuzziness': 2,
            'fuzzy_transpositions': True,
        }})


class QueryStringField(ElasicField, fields.String):
    @property
    def query_fields(self):
        return self.metadata.get('query_fields', [])

    def q(self, value):
        params = {
            'query': value,
            'fuzzy_transpositions': True,
            'fuzziness': 2
        }
        if self.query_fields:
            params['fields'] = self.query_fields
        else:
            params['all_fields'] = True

        return Q('query_string', **params)


class SimpleQueryStringField(ElasicField, fields.String):
    @property
    def query_fields(self):
        return self.metadata.get('query_fields', list(self.query_field_name))

    def q(self, value):
        return Q('simple_query_string', **{
            'fields': self.query_fields,
            'query': value,
            'fuzzy_transpositions': True,
            'fuzziness': 2
        })


class MultiMatchField(ElasicField, fields.List):
    def __init__(self, cls_or_instance=fields.String, **kwargs):
        super().__init__(cls_or_instance, **kwargs)

    @fields.before_deserialize
    def prepare_value(self, value=None, attr=None, data=None):
        if not isinstance(value, collections.Iterable) or isinstance(value, (str, bytes)):
            value = [value, ]

        value = flatten_list(value, split_delimeter=',')
        return value, attr, data

    @property
    def query_fields(self):
        lang = get_language()
        trans_fields = []
        for field in self.metadata.get('query_fields', []):
            m = re.search(r'^(?P<base>\w+)\.?(?P<nested>[\.\w]*)?(?P<prior>\^\d+)?', field)
            parts = [m.group('base'), lang]
            if m.group('nested'):
                parts.append(m.group('nested'))
            trans_field = '.'.join(parts)
            if m.group('prior'):
                trans_field += m.group('prior')
            trans_fields.append(trans_field)
        print(trans_fields)
        return trans_fields

    @property
    def nested_query_fields(self):
        return self.metadata.get('nested_query_fields', {})

    def q(self, data):
        queries = []
        for query_string in data:
            queries.append(
                Q("multi_match", **{
                    'fields': self.query_fields,
                    'query': query_string,
                    'fuzziness': 2,
                    'fuzzy_transpositions': True
                })
            )

            for path, _fields in self.nested_query_fields.items():
                _queries = []
                q_fields = ["{}.{}".format(path, field) for field in _fields]
                _queries.append(
                    Q('multi_match', **{
                        'query': query_string,
                        'fields': q_fields,
                        'fuzziness': 2,
                        'fuzzy_transpositions': True
                    })
                )

                queries.append(
                    Q(
                        "nested",
                        path=path,
                        query=functools.reduce(operator.or_, _queries)
                    )
                )
        return queries

    def _prepare_queryset(self, queryset, data):
        return queryset.query('bool', should=data) if data else queryset


class SortField(ElasicField, fields.List):
    def __init__(self, cls_or_instance=fields.String, **kwargs):
        super().__init__(cls_or_instance, **kwargs)

    def _prepare_queryset(self, queryset, data):
        return queryset.sort(*data)

    @property
    def sort_fields(self):
        return self.metadata.get('sort_fields', [])

    def q(self, sort_params):
        data = []
        for param in sort_params:
            direction = '-' if param.startswith('-') else '+'
            field_name = param.lstrip(direction).strip()

            if field_name in self.sort_fields:
                field_path = self.sort_fields[field_name]
                if '{lang}' in field_path:
                    field_path = field_path.format(lang=get_language())
                    nested_path = field_path.split('.')[0]
                    sort_opt = {
                        field_path: {
                            'order': 'desc' if direction == '-' else 'asc',
                            'nested': {
                                'path': nested_path
                            }
                        }
                    }
                else:
                    sort_opt = {field_path: {'order': 'desc' if direction == '-' else 'asc'}}

                data.append(sort_opt)

        return data

    @fields.before_deserialize
    def prepare_value(self, value=None, attr=None, data=None):
        if not isinstance(value, collections.Iterable) or isinstance(value, (str, bytes)):
            value = [value, ]

        value = flatten_list(value, split_delimeter=',')
        return value, attr, data


class SuggestField(ElasicField, fields.String):
    @property
    def suggester_name(self):
        return self.metadata.get('suggester_name', 'suggest-{}'.format(self.query_field_name))

    @property
    def suggester_type(self):
        return self.metadata.get('suggester_type', 'term')

    def q(self, value):
        return value

    def _prepare_queryset(self, queryset, text):
        return queryset.suggest(self.suggester_name, text, **{
            self.suggester_type: {'field': self.query_field_name}
        })


class AggregationField(ElasicField, fields.String):
    def _prepare_queryset(self, queryset, data):
        for name, facet in data:
            agg = facet.get_aggregation()
            agg_filter = Q('match_all')
            agg_name = '_filter_'+name
            queryset.aggs.bucket(
                agg_name,
                'filter',
                filter=agg_filter
            ).bucket(name, agg)
        return queryset

    def q(self, value):
        return value


class TermsAggregationField(AggregationField):
    def q(self, value):
        res = []
        _d = self._metadata.get('aggs', {})
        for facet_name in value.split(','):
            if facet_name in _d:
                _f = dict(_d[facet_name])
                _field = _f['field']
                _path = _f.get('nested_path', None)
                kw = {
                    'size': _f.get('size', 500),
                    'min_doc_count': _f.get('min_doc_count', 1)
                }
                _order = _f.get('order')
                if _order:
                    kw['order'] = _order
                _missing = _f.get('missing')
                if _missing:
                    kw['missing'] = _missing
                _facet = TermsFacet(field=_field, **kw)
                facet = NestedFacet(_path, _facet) if _path else _facet
                res.append(
                    (facet_name, facet)
                )

        return res


class DateHistogramAggregationField(AggregationField):
    def q(self, value):
        res = []
        _d = self._metadata.get('aggs', {})
        for facet_name in value.split(','):
            if facet_name in _d:
                _f = dict(_d[facet_name])
                _field = _f['field']
                _path = _f.get('nested_path', None)
                kw = {
                    'size': _f.get('size', 500),
                    'min_doc_count': _f.get('min_doc_count', 1),
                    'interval': _f.get('interval', None),
                    'keyed': _f.get('keyed', False)
                }
                _order = _f.get('order')
                if _order:
                    kw['order'] = _order
                _format = _f.get('format')
                if _format:
                    kw['format'] = _format
                _missing = _f.get('missing')
                if _missing:
                    kw['missing'] = _missing

                _facet = TermsFacet(field=_field, **kw)
                facet = NestedFacet(_path, _facet) if _path else _facet
                res.append(
                    (facet_name, facet)
                )

        return res


# class TermsAggregationField(ElasicField, fields.)

# class FilterAggregationField(ElasicField, fields.List):
#     @fields.before_deserialize
#     def prepare_value(self, value=None, attr=None, data=None):
#         if not isinstance(value, collections.Iterable) or isinstance(value, (str, bytes)):
#             value = [value, ]
#
#         value = flatten_list(value, split_delimeter=',')
#         return value, attr, data
#
#     def q(self, value):


class NumberField(ElasicField, fields.Integer):
    def _prepare_queryset(self, queryset, data):
        return queryset

    def q(self, value):
        return value


class StringField(ElasicField, fields.String):
    def _prepare_queryset(self, queryset, data):
        return queryset

    def q(self, value):
        return value

# class FacetFilterField(FilterField):
#     pass

# FacetFilterField

# IdsSearchField
# HighlightBackendField
