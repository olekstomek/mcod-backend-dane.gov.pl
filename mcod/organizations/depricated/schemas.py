# coding: utf-8
from elasticsearch_dsl import TermsFacet

from mcod.lib import fields
from mcod.lib.schemas import List
from mcod.core.api.search import constants


class InstitutionsList(List):
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

    city = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_WILDCARD,
        constants.LOOKUP_FILTER_PREFIX,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,

    ])
    regon = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_WILDCARD,
        constants.LOOKUP_FILTER_PREFIX,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,

    ])
    street = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_WILDCARD,
        constants.LOOKUP_FILTER_PREFIX,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,

    ])
    postal_code = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_WILDCARD,
        constants.LOOKUP_FILTER_PREFIX,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,

    ])
    email = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_WILDCARD,
        constants.LOOKUP_FILTER_PREFIX,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,

    ])
    type = fields.FilteringFilterField(field_name='institution_type', lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
    ])
    tel = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_WILDCARD,
        constants.LOOKUP_FILTER_PREFIX,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,

    ])
    fax = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_WILDCARD,
        constants.LOOKUP_FILTER_PREFIX,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,

    ])
    website = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_WILDCARD,
        constants.LOOKUP_FILTER_PREFIX,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,
    ])

    title = fields.SearchFilterField(search_i18n_fields=['title'])

    description = fields.SearchFilterField(search_i18n_fields=['description'])

    q = fields.SearchFilterField(
        search_i18n_fields=['title', 'description'],
    )

    facet = fields.FacetedFilterField(
        facets={
            'cities': TermsFacet(field='city', size=500),
            'types': TermsFacet(field='institution_type', size=500)
        },
    )

    title_suggest = fields.SuggesterFilterField(
        field='title.suggest',
        suggesters=[
            constants.SUGGESTER_COMPLETION,
            constants.SUGGESTER_PHRASE,
            constants.SUGGESTER_TERM
        ]
    )
    sort = fields.OrderingFilterField(
        ordering_fields={
            "id": "id",
            "title": "title.{lang}.sort",
            "city": "city",
            "modified": "modified",
            "created": "created"
        }
    )

    #
    # highlight = fields.HighlightBackend(
    #     highlight_fields={
    #         'title': {
    #             'options': {
    #                 'pre_tags': ['<em>'],
    #                 'post_tags': ['</em>'],
    #             },
    #             'enabled': True
    #         },
    #         'notes': {
    #             'options': {
    #                 'pre_tags': ['<em>'],
    #                 'post_tags': ['</em>'],
    #             },
    #             'enabled': True
    #         }
    #     }
    # )

    class Meta:
        strict = True
