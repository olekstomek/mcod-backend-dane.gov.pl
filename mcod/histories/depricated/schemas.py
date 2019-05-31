# coding: utf-8
# from elasticsearch_dsl import TermsFacet

from mcod.lib import fields
from mcod.lib.schemas import List
from mcod.core.api.search import constants


class HistoriesList(List):
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

    table_name = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_FILTER_REGEXP,
        constants.LOOKUP_QUERY_CONTAINS,
        constants.LOOKUP_QUERY_ENDSWITH,
        constants.LOOKUP_QUERY_STARTSWITH
    ])

    row_id = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,
        constants.LOOKUP_QUERY_LTE,
    ])

    action = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        # constants.LOOKUP_QUERY_IN,
    ])

    old_value = fields.FilteringFilterField()
    new_value = fields.FilteringFilterField()
    difference = fields.FilteringFilterField()
    change_user_id = fields.FilteringFilterField(lookups=[
        constants.LOOKUP_FILTER_TERM,
        constants.LOOKUP_FILTER_TERMS,
        constants.LOOKUP_QUERY_IN,
        constants.LOOKUP_QUERY_GT,
        constants.LOOKUP_QUERY_GTE,
        constants.LOOKUP_QUERY_LT,
        constants.LOOKUP_QUERY_LTE,
    ]
    )
    change_timestamp = fields.FilteringFilterField()
    message = fields.FilteringFilterField()

    q = fields.SearchFilterField(
        search_fields=['table_name', 'action'],
    )

    sort = fields.OrderingFilterField(
        ordering_fields={
            "id": "id",
            "row_id": "row_id",
            "table_name": "table_name",
            "change_timestamp": "change_timestamp",
            "change_user_id": "change_user_id"
        }
    )

    class Meta:
        strict = True
