from django.utils.translation import get_language, gettext_lazy as _
from elasticsearch_dsl import Search, MultiSearch
from marshmallow import validates, ValidationError, validate

from mcod import settings
from mcod.core.api.jsonapi.deserializers import TopLevel, ObjectAttrs
from mcod.core.api import fields as core_fields
from mcod.core.api.schemas import (
    CommonSchema,
    DateTermSchema,
    ExtSchema,
    ListingSchema,
    ListTermsSchema,
    NumberTermSchema,
    StringTermSchema,
    StringMatchSchema,
    BooleanTermSchema
)
from mcod.core.api.search import fields
from mcod.datasets.deserializers import (
    InstitutionFilterSchema,
    CategoryFilterSchema as DatasetCategoryFilterSchema,
    CategoriesFilterSchema as DatasetCategoriesFilterSchema,
    RegionsFilterSchema
)

from mcod.search.fields import (
    CommonSearchField,
    get_advanced_options,
    nested_query_with_advanced_opts,
)
from mcod.unleash import is_enabled

SPARQL_FORMATS = {
    # europeandataportal format choices: rdflib.SparqlStore valid params.
    'application/rdf+xml': 'application/rdf+xml',
    'text/turtle': 'application/rdf+xml',
    'text/csv': 'csv',
    # 'text/tsv': 'tsv',  # no tsv at https://www.europeandataportal.eu/sparql-manager/pl/ .
    'application/sparql-results+json': 'json',
    'application/sparql-results+xml': 'xml',
}
SPARQL_FORMAT_CHOICES = SPARQL_FORMATS.keys()

SPARQL_ENDPOINTS = list(settings.SPARQL_ENDPOINTS.keys())


class SourceFilterSchema(ExtSchema):
    title = fields.FilterField(StringMatchSchema, search_path='source', nested_search=True,
                               query_field='source.title')
    type = fields.FilterField(StringMatchSchema, search_path='source', nested_search=True,
                              query_field='source.type')
    update_frequency = fields.FilterField(StringMatchSchema, search_path='source', nested_search=True,
                                          query_field='source.update_frequency')

    class Meta:
        default_field = 'term'


class DataAggregations(ExtSchema):
    terms = fields.TermsAggregationField(
        aggs={
            'by_institution': {
                'field': 'institution.id',
                'size': 500,
                'nested_path': 'institution',
            },
            'by_category': {
                'field': 'category.id',
                'nested_path': 'category',
                'size': 100
            },
            'by_categories': {
                'field': 'categories.id',
                'nested_path': 'categories',
                'size': 100
            },
            'by_format': {
                'size': 500,
                'field': 'formats'
            },
            'by_openness_score': {
                'size': 500,
                'field': 'openness_scores'
            },
            'by_types': {
                'field': 'types',
                'size': 100
            },
            'by_visualization_types': {
                'field': 'visualization_types',
                'size': 100
            },
            'by_institution_type': {
                'field': 'institution_type',
                'size': 10
            },
            'by_license_code': {
                'field': 'license_code',
                'size': 100
            },
            'by_update_frequency': {
                'field': 'update_frequency',
                'size': 100
            },
            'by_has_high_value_data': {
                'field': 'has_high_value_data',
                'size': 100
            },
            'by_showcase_category': {
                'field': 'showcase_category',
                'size': 10
            },
            'by_showcase_types': {
                'field': 'showcase_types',
                'size': 10
            },
            'by_showcase_platforms': {
                'field': 'showcase_platforms',
                'size': 10
            },
        }
    )

    date_histogram = fields.DateHistogramAggregationField(
        aggs={
            'by_modified': {
                'field': 'modified',
                'size': 500
            },
            'by_created': {
                'field': 'created',
                'size': 500
            },
            'by_verified': {
                'field': 'verified',
                'size': 500
            }
        }
    )

    date_range = fields.MetricRangeAggregationField(
        aggs={
            'max': {
                'field': 'search_date'
            },
            'min': {
                'field': 'search_date'
            }
        }
    )


class ApiSearchRequest(ListingSchema):
    q = CommonSearchField(
        doc_template='docs/generic/fields/query_field.html',
        doc_base_url='/search',
        doc_field_name='q'
    )

    advanced = fields.StringField()
    sort = fields.SortField(
        sort_fields={
            'title': 'title.{lang}.sort',
            'date': 'search_date',
            'views_count': 'views_count',
        },
        doc_base_url='/search',
    )

    facet = fields.FacetField(DataAggregations)

    id = fields.FilterField(
        StringTermSchema,
        doc_template='docs/generic/fields/number_term_field.html',
        doc_base_url='/search',
        doc_field_name='ID',
        query_field='_id',
    )
    model = fields.FilterField(
        StringTermSchema,
        doc_template='docs/search/fields/model.html',
        doc_base_url='/search',
        doc_field_name='models',
    )
    institution = fields.FilterField(InstitutionFilterSchema)
    category = fields.FilterField(DatasetCategoryFilterSchema)
    categories = fields.FilterField(DatasetCategoriesFilterSchema)
    format = fields.FilterField(
        StringTermSchema,
        doc_template='docs/generic/fields/string_term_field.html',
        doc_base_url='/search',
        doc_field_name='format',
        query_field='formats'
    )
    types = fields.FilterField(
        StringTermSchema,
        doc_template='docs/generic/fields/string_term_field.html',
        doc_base_url='/search',
        doc_field_name='types',
    )
    openness_score = fields.FilterField(
        NumberTermSchema,
        doc_template='docs/generic/fields/number_term_field.html',
        doc_base_url='/search',
        doc_field_name='openness score',
        query_field='openness_scores'
    )
    visualization_types = fields.FilterField(
        ListTermsSchema,
        query_field='visualization_types',
        doc_template='docs/generic/fields/string_term_field.html',
        doc_base_url='/search',
        doc_field_name='visualization type'
    )
    date = fields.FilterField(
        DateTermSchema,
        query_field='search_date',
        doc_template='docs/generic/fields/number_term_field.html',
        doc_base_url='/search',
        doc_field_name='search_date'
    )
    institution_type = fields.FilterField(
        StringTermSchema,
        query_field='institution_type',
        doc_template='docs/generic/fields/string_term_field.html',
        doc_base_url='/search',
        doc_field_name='institution_type'
    )
    source = fields.FilterField(SourceFilterSchema)
    license_code = fields.FilterField(
        NumberTermSchema,
        doc_template='docs/generic/fields/number_term_field.html',
        doc_base_url='/search',
        doc_field_name='license code',
        query_field='license_code'
    )
    update_frequency = fields.FilterField(
        StringTermSchema,
        query_field='update_frequency',
        doc_template='docs/generic/fields/string_term_field.html',
        doc_base_url='/search',
        doc_field_name='update_frequency'
    )
    has_high_value_data = fields.FilterField(
        BooleanTermSchema,
        query_field='has_high_value_data',
        doc_template='docs/generic/fields/boolean_term_field.html',
        doc_base_url='/search',
        doc_field_name='has_high_value_data'
    )
    if is_enabled('S39_filter_by_geodata.be'):
        regions = fields.FilterField(RegionsFilterSchema)
    if is_enabled('S39_showcases.be'):
        showcase_category = fields.FilterField(
            ListTermsSchema,
            doc_template='docs/generic/fields/string_term_field.html',
            doc_base_url='/search',
            doc_field_name='showcase_category',
        )
        showcase_types = fields.FilterField(
            ListTermsSchema,
            query_field='showcase_types',
            doc_template='docs/generic/fields/string_term_field.html',
            doc_base_url='/search',
            doc_field_name='showcase types'
        )
        showcase_platforms = fields.FilterField(
            ListTermsSchema,
            query_field='showcase_platforms',
            doc_template='docs/generic/fields/string_term_field.html',
            doc_base_url='/search',
            doc_field_name='showcase platforms'
        )

    @validates('q')
    def validate_q(self, queries, down_limit=2, up_limit=3000):
        for q in queries:
            if len(q) < down_limit:
                msg = _('The entered phrase should be at least %(limit)s characters long') % {'limit': down_limit}
                raise ValidationError(msg)
            elif len(q) > up_limit:
                msg = _('The entered phrase should be at most %(limit)s characters long') % {'limit': up_limit}
                raise ValidationError(msg)

    @validates('advanced')
    def validate_advanced(self, adv):
        allowed = ('any', 'all', 'exact', 'synonyms')
        if adv not in allowed:
            msg = _('Advanced option should take one of values: ') + ', '.join(allowed)
            raise ValidationError(msg)

    class Meta:
        strict = True
        ordered = True


class SparqlRequestAttrs(ObjectAttrs):
    q = core_fields.String(required=True, description='Sparql query', example='Looks unpretty')
    format = core_fields.Str(
        required=True, validate=validate.OneOf(
            choices=SPARQL_FORMAT_CHOICES,
            error=_('Unsupported format. Supported are: %(formats)s') % {'formats': ', '.join(SPARQL_FORMAT_CHOICES)}))
    page = core_fields.Int()
    per_page = core_fields.Int()
    external_sparql_endpoint = core_fields.Str(
        validate=validate.OneOf(
            choices=SPARQL_ENDPOINTS,
            error=_('Unsupported SPARQL endpoint value. Supported values are: %(providers)s') % {
                'providers': ', '.join(SPARQL_ENDPOINTS)},
        ),
        allow_none=True)

    class Meta:
        strict = True
        ordered = True
        object_type = 'sparql'


class SparqlRequest(TopLevel):
    class Meta:
        attrs_schema = SparqlRequestAttrs
        attrs_schema_required = True


class ApiSuggestRequest(CommonSchema):
    q = fields.StringField()
    per_model = fields.NumberField(
        missing=1,
        default=1,
        example=2,
        description='Suggestion size for each model. Default value is 1, max allowed page size is 10.',
        validate=validate.Range(1, 10, error=_("Invalid suggestion size"))
    )
    max_length = fields.NumberField(
        missing=1,
        example=2,
        description='Maximum length of given suggestion list. By default there is no limit',
        validate=validate.Range(1, 100, error=_("Invalid maximum list length"))
    )
    if is_enabled('S39_showcases.be'):
        _supported_models = {'dataset', 'resource', 'institution', 'article', 'knowledge_base', 'showcase'}
    else:
        _supported_models = {'dataset', 'resource', 'institution', 'article', 'knowledge_base', 'application'}
    _completion_models = {'region'}
    models = fields.StringField()
    advanced = fields.StringField()

    def __init__(self, *args, **kwargs):
        if is_enabled('S39_filter_by_geodata.be'):
            self._supported_models.add('region')
        super(ApiSuggestRequest, self).__init__(*args, **kwargs)

    def get_queryset(self, queryset, data):
        phrase = data.get('q')

        if 'models' not in data:
            models = self._supported_models
        else:
            models = data['models'].split(',')

        advanced = data.get('advanced')
        op, suffix = get_advanced_options(advanced)
        lang = get_language()

        per_model = data.get('per_model', 1)
        ms = MultiSearch(index=settings.ELASTICSEARCH_COMMON_ALIAS_NAME)

        for model in models:
            if is_enabled('S39_filter_by_geodata.be') and model in self._completion_models:
                sug_query = Search(index=f'{model}s')
                sug_query = sug_query.suggest('title', phrase,
                                              completion={'field': f'title.{lang}.suggest', 'size': per_model})
                res = sug_query.execute()
                suggestions = res.suggest['title'][0]
                ids = [sug['_id'] for sug in suggestions['options']]
                query = Search(index=settings.ELASTICSEARCH_COMMON_ALIAS_NAME)
                query = query.filter('term', model=model).query('ids', values=ids)
            else:
                query = Search(index=settings.ELASTICSEARCH_COMMON_ALIAS_NAME)
                query = query.filter('term', model=model)
                query = query.query('bool',
                                    should=[nested_query_with_advanced_opts(phrase, field, lang, op, suffix)
                                            for field in ('title', 'notes')])
                query = query.extra(size=per_model)
            ms = ms.add(query)

        return ms

    @validates('models')
    def validate_models(self, models):
        for model in models.split(','):
            if model not in self._supported_models:
                msg = _('The entered model - %(model)s, is not supported') % {'model': model}
                raise ValidationError(msg)

    @validates('advanced')
    def validate_advanced(self, adv):
        if adv not in 'any all exact synonyms'.split():
            msg = _('advanced option should take one of values: any, all, exact, synonyms')
            raise ValidationError(msg)

    class Meta:
        strict = True
        ordered = False
