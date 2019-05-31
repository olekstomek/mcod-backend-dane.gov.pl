from mcod.core.api.schemas import ListingSchema, CommonSchema, ExtSchema
from mcod.core.api.schemas import NumberTermSchema, StringTermSchema, StringMatchSchema
from mcod.core.api.search import fields as search_fields


class InstitutionApiAggregations(ExtSchema):
    term = search_fields.TermsAggregationField(
        aggs={
            'by_city': {
                'field': 'city',
                'size': 500,
            },
            'by_instytution_type': {
                'field': 'institution_type',
                'size': 10
            }
        }
    )


class InstitutionApiSearchRequest(ListingSchema):
    id = search_fields.FilterField(NumberTermSchema,
                                   doc_template='docs/generic/fields/number_term_field.html',
                                   doc_base_url='/institutions',
                                   doc_field_name='ID'
                                   )
    slug = search_fields.FilterField(StringTermSchema,
                                     doc_template='docs/generic/fields/string_term_field.html',
                                     doc_base_url='/institutions',
                                     doc_field_name='slug',
                                     translated=True,
                                     search_path='slug'
                                     )
    city = search_fields.FilterField(StringTermSchema,
                                     doc_template='docs/generic/fields/string_term_field.html',
                                     doc_base_url='/institutions',
                                     doc_field_name='city'
                                     )
    regon = search_fields.FilterField(StringTermSchema,
                                      doc_template='docs/generic/fields/string_term_field.html',
                                      doc_base_url='/institutions',
                                      doc_field_name='regon'
                                      )
    street = search_fields.FilterField(StringTermSchema,
                                       doc_template='docs/generic/fields/string_term_field.html',
                                       doc_base_url='/institutions',
                                       doc_field_name='street'
                                       )
    postal_code = search_fields.FilterField(StringTermSchema,
                                            doc_template='docs/generic/fields/string_term_field.html',
                                            doc_base_url='/institutions',
                                            doc_field_name='postal code'
                                            )

    email = search_fields.FilterField(StringTermSchema,
                                      doc_template='docs/generic/fields/string_term_field.html',
                                      doc_base_url='/institutions',
                                      doc_field_name='email address'
                                      )
    org_type = search_fields.FilterField(StringTermSchema,
                                         data_key='type',
                                         doc_template='docs/generic/fields/string_term_field.html',
                                         doc_base_url='/institutions',
                                         doc_field_name='type'
                                         )
    tel = search_fields.FilterField(StringTermSchema,
                                    doc_template='docs/generic/fields/string_term_field.html',
                                    doc_base_url='/institutions',
                                    doc_field_name='tel'
                                    )
    fax = search_fields.FilterField(StringTermSchema,
                                    doc_template='docs/generic/fields/string_term_field.html',
                                    doc_base_url='/institutions',
                                    doc_field_name='fax'
                                    )
    website = search_fields.FilterField(StringTermSchema,
                                        doc_template='docs/generic/fields/string_term_field.html',
                                        doc_base_url='/institutions',
                                        doc_field_name='website'
                                        )

    title = search_fields.FilterField(StringMatchSchema,
                                      doc_template='docs/generic/fields/string_match_field.html',
                                      doc_base_url='/institutions',
                                      doc_field_name='title',
                                      translated=True,
                                      search_path='title'

                                      )
    description = search_fields.FilterField(StringMatchSchema,
                                            doc_template='docs/generic/fields/string_match_field.html',
                                            doc_base_url='/institutions',
                                            doc_field_name='description',
                                            translated=True,
                                            search_path='title'
                                            )

    q = search_fields.MultiMatchField(
        query_fields=['title^4', 'description^2'],
        nested_query_fields={'datasets': ['title', ]},
        doc_template='docs/generic/fields/query_field.html',
        doc_base_url='/institutions',
        doc_field_name='q'
    )
    sort = search_fields.SortField(
        sort_fields={
            'id': 'id',
            'title': 'title.{lang}.sort',
            "city": "city.{lang}",
            'modified': 'modified',
            'created': 'created'
        },
        doc_template='docs/generic/fields/sort_field.html',
        doc_base_url='/institutions',
        doc_field_name='sort'
    )
    facet = search_fields.FacetField(InstitutionApiAggregations)

    class Meta:
        strict = True
        ordered = True


class InstitutionApiRequest(CommonSchema):
    id = search_fields.NumberField(
        _in='path', description='Institution ID', example='44', required=True
    )

    class Meta:
        strict = True
        ordered = True
