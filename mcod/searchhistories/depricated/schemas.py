# coding: utf-8

from mcod.lib import fields
from mcod.lib.schemas import List
from mcod.core.api.search import constants


class SearchHistoriesList(List):
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

    url = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_REGEXP,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_ENDSWITH,
        constants.LOOKUP_QUERY_STARTSWITH
    ])

    query_sentence = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_REGEXP,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_ENDSWITH,
        constants.LOOKUP_QUERY_STARTSWITH
    ])

    user = fields.NestedFilteringField('user', field_name='user.id', lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,

    ]
    )

    modfied = fields.FilteringFilterField()

    q = fields.SearchFilterField(
        search_fields=['query_sentence', 'url'],
    )

    sort = fields.OrderingFilterField(
        ordering_fields={
            "id": "id",
            "query_sentence": "query_sentence_keyword",
            "modified": "modified",
            "user": "user.id"
        }
    )

    class Meta:
        strict = True
