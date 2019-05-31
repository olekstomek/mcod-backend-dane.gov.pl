# coding: utf-8
from elasticsearch_dsl import DateHistogramFacet, TermsFacet

from mcod.lib import fields
from mcod.lib.schemas import List
from mcod.core.api.search import constants


class ArticlesList(List):
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

    slug = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_EXCLUDE,
        constants.LOOKUP_QUERY_STARTSWITH,
        constants.LOOKUP_QUERY_ENDSWITH,
    ])

    category = fields.NestedFilteringField('category', field_name='category.id', lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,
        constants.LOOKUP_QUERY_LTE,
        constants.LOOKUP_QUERY_IN
    ])

    facet = fields.FacetedFilterField(
        facets={
            'tags': TermsFacet(field='tags', size=500),
            'modified': DateHistogramFacet(field='modified', interval='month', size=500)
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
