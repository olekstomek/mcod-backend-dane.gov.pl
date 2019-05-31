# coding: utf-8
from elasticsearch_dsl import TermsFacet

from mcod.lib import fields
from mcod.lib.schemas import List
from mcod.core.api.search import constants


class ResourcesList(List):
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

    uuid = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,
    ])

    ids = fields.IdsSearchField()

    title = fields.SearchFilterField(search_i18n_fields=['title'])

    description = fields.SearchFilterField(search_i18n_fields=['description'])

    dataset = fields.NestedFilteringField('dataset', field_name='dataset.id', lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,
        constants.LOOKUP_QUERY_LTE,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_EXCLUDE,
    ])

    formats = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
    ])

    type = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
    ])

    openness_score = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,
        constants.LOOKUP_QUERY_LTE,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
    ])

    q = fields.SearchFilterField(
        search_i18n_fields=['title', 'description'],
    )

    facet = fields.FacetedFilterField(
        facets={
            'formats': TermsFacet(field='formats', size=500),
            'types': TermsFacet(fields='type', size=500),
            'openness_score': TermsFacet(field='openness_score', size=500)
        },
    )

    sort = fields.OrderingFilterField(
        ordering_fields={
            "id": "id",
            "title": "title.{lang}.sort",
            "modified": "modified",
            "created": "created",
            "verified": "verified",
            "data_date": "data_date"

        }
    )

    class Meta:
        strict = True
