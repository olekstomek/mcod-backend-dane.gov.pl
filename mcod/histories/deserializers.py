from mcod.core.api.search import fields as search_fields
from mcod.core.api.schemas import CommonSchema, DateTermSchema, ListingSchema, NumberTermSchema, StringMatchSchema


class HistoryApiRequest(CommonSchema):
    id = search_fields.NumberField(
        _in='path', description='History ID', example='1', required=True
    )

    class Meta:
        strict = True
        ordered = True


class HistoryApiSearchRequest(ListingSchema):
    id = search_fields.FilterField(
        NumberTermSchema,
        doc_template='docs/generic/fields/number_term_field.html',
        doc_base_url='/histories',
        doc_field_name='ID',
    )
    action = search_fields.FilterField(
        StringMatchSchema,
        doc_template='docs/generic/fields/string_match_field.html',
        doc_base_url='/histories',
        doc_field_name='action',
    )
    change_user_id = search_fields.FilterField(
        NumberTermSchema,
        doc_template='docs/generic/fields/number_term_field.html',
        doc_base_url='/histories',
        doc_field_name='change_user_id',
    )
    change_timestamp = search_fields.FilterField(
        DateTermSchema,
        doc_template='docs/generic/fields/number_term_field.html',
        doc_base_url='/histories',
        doc_field_name='change_timestamp',
    )
    message = search_fields.FilterField(
        StringMatchSchema,
        doc_template='docs/generic/fields/string_match_field.html',
        doc_base_url='/histories',
        doc_field_name='message',
    )
    q = search_fields.MultiMatchField(extra_fields=['table_name', 'action'])
    row_id = search_fields.FilterField(
        NumberTermSchema,
        doc_template='docs/generic/fields/number_term_field.html',
        doc_base_url='/histories',
        doc_field_name='row_id',
    )
    sort = search_fields.SortField(
        sort_fields={
            'id': 'id',
            'row_id': 'row_id',
            'table_name': 'table_name',
            'change_timestamp': 'change_timestamp',
            'change_user_id': 'change_user_id',
        },
        doc_base_url='/histories',
    )
    table_name = search_fields.FilterField(
        StringMatchSchema,
        doc_template='docs/generic/fields/string_match_field.html',
        doc_base_url='/histories',
        doc_field_name='table_name',
    )

    class Meta:
        strict = True
        ordered = True
