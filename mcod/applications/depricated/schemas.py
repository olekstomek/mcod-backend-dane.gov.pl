# coding: utf-8
from django.conf import settings
from elasticsearch_dsl import DateHistogramFacet, TermsFacet
from marshmallow import Schema

from mcod.core.api.search import constants
from mcod.lib import fields
from mcod.lib.schemas import List


class ApplicationsList(List):
    id = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,
        constants.LOOKUP_QUERY_LTE,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_EXCLUDE,
    ])
    ids = fields.IdsSearchField()

    slug = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,
    ])

    title = fields.SearchFilterField(search_i18n_fields=['title'])
    notes = fields.SearchFilterField(search_i18n_fields=['notes'])

    q = fields.SearchFilterField(
        search_i18n_fields=['title', 'notes', 'datasets.title'],
    )

    tags = fields.FilteringFilterField(
        lookups=[
            constants.LOOKUP_FILTER_TERM,
            constants.LOOKUP_FILTER_TERMS,
            constants.LOOKUP_FILTER_WILDCARD,
            constants.LOOKUP_FILTER_PREFIX,
            constants.LOOKUP_QUERY_IN,
            constants.LOOKUP_QUERY_EXCLUDE,
            constants.LOOKUP_QUERY_CONTAINS
        ],
        translated=True
    )

    author = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_WILDCARD,
        constants.LOOKUP_FILTER_PREFIX,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,
    ])

    facet = fields.FacetedFilterField(
        facets={
            'tags': TermsFacet(field='tags', size=500),
            'modified': DateHistogramFacet(field='modified', interval='month', size=500)
        },
    )

    sort = fields.OrderingFilterField(
        default_ordering=['-modified', ],
        ordering_fields={
            "id": "id",
            "title": "title.{lang}.sort",
            "modified": "modified",
            "created": "created"
        }
    )

    highlight = fields.HighlightBackend(
        highlight_fields={
            'title': {
                'options': {
                    'pre_tags': ['<em>'],
                    'post_tags': ['</em>'],
                },
                'enabled': True
            },
            'notes': {
                'options': {
                    'pre_tags': ['<em>'],
                    'post_tags': ['</em>'],
                },
                'enabled': True
            }
        }
    )

    class Meta:
        strict = True


class ApplicationExternalData(Schema):
    title = fields.Str(required=False)
    url = fields.Url(required=False)


class ApplicationSuggestion(Schema):
    applicant_email = fields.Email(required=False)
    author = fields.Str(required=False)
    title = fields.Str(required=True, faker_type='application title', example='Some App')
    url = fields.Url(required=True)
    notes = fields.Str(required=True)
    image = fields.Base64(required=False, max_size=settings.IMAGE_UPLOAD_MAX_SIZE)
    datasets = fields.List(fields.Int(), required=False)
    external_datasets = fields.Nested(ApplicationExternalData, required=False, many=True)
    keywords = fields.List(fields.Str(), required=False)

    class Meta:
        strict = True
