# coding: utf-8
from elasticsearch_dsl import TermsFacet

from mcod.core.api.search import constants
from mcod.core.api.search.facets import NestedFacet
from mcod.lib import fields
from mcod.lib.schemas import List


class DatasetsList(List):
    id = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,
        constants.LOOKUP_QUERY_LTE,
        constants.LOOKUP_QUERY_IN
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

    category = fields.NestedFilteringField('category', field_name='category.id', lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,
        constants.LOOKUP_QUERY_LTE,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_EXCLUDE,
    ])

    institution = fields.NestedFilteringField('institution', field_name='institution.id', lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,
        constants.LOOKUP_QUERY_LTE,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_EXCLUDE,
    ])

    tags = fields.FilteringFilterField(
        lookups=[
            constants.LOOKUP_FILTER_TERM,
            constants.LOOKUP_FILTER_TERMS,
            constants.LOOKUP_FILTER_WILDCARD,
            constants.LOOKUP_FILTER_PREFIX,
            constants.LOOKUP_QUERY_IN,
            constants.LOOKUP_QUERY_EXCLUDE,
            constants.LOOKUP_QUERY_CONTAINS,
        ],
        translated=True
    )

    formats = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
    ])

    openness_scores = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_WILDCARD,
        constants.LOOKUP_FILTER_PREFIX,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_CONTAINS
    ])

    q = fields.SearchFilterField(
        search_i18n_fields=['title', 'notes'],
    )

    facet = fields.FacetedFilterField(
        facets={
            'institutions': NestedFacet('institution', TermsFacet(field='institution.id', size=500)),
            'categories': NestedFacet('category', TermsFacet(field='category.id', size=500)),
            'tags': TermsFacet(field='tags', size=500),
            'formats': TermsFacet(field='formats', size=500),
            'openness_scores': TermsFacet(field='openness_scores')
        },
    )

    views_count = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,
        constants.LOOKUP_QUERY_LTE,
    ])

    sort = fields.OrderingFilterField(
        ordering_fields={
            "id": "id",
            "title": "title.{lang}.sort",
            "modified": "last_modified_resource",
            "created": "created",
            "views_count": "views_count",
            "verified": "verified",
        }
    )

    class Meta:
        strict = True
