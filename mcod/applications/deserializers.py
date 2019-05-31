from mcod import settings
from mcod.core.api import fields as core_fields
from mcod.core.api.jsonapi.deserializers import TopLevel, ObjectAttrs
from mcod.core.api.schemas import ListingSchema, CommonSchema, ExtSchema
from mcod.core.api.schemas import NumberTermSchema, StringTermSchema, StringMatchSchema
from mcod.core.api.search import fields as search_fields


class ApplicationAggs(ExtSchema):
    date_histogram = search_fields.DateHistogramAggregationField(
        aggs={
            'by_modified': {
                'field': 'modified',
                'size': 500
            },
            'by_created': {
                'field': 'created',
                'size': 500
            }
        }
    )


class ApplicationApiSearchRequest(ListingSchema):
    id = search_fields.FilterField(NumberTermSchema,
                                   doc_template='docs/generic/fields/number_term_field.html',
                                   doc_base_url='/datasets',
                                   doc_field_name='ID'
                                   )
    title = search_fields.FilterField(StringMatchSchema,
                                      doc_template='docs/generic/fields/string_match_field.html',
                                      doc_base_url='/datasets',
                                      doc_field_name='title',
                                      translated=True,
                                      search_path='title'
                                      )
    notes = search_fields.FilterField(StringMatchSchema,
                                      doc_template='docs/generic/fields/string_match_field.html',
                                      doc_base_url='/datasets',
                                      doc_field_name='notes',
                                      translated=True,
                                      search_path='notes'
                                      )

    tag = search_fields.FilterField(StringTermSchema,
                                    doc_template='docs/generic/fields/string_term_field.html',
                                    doc_base_url='/datasets',
                                    doc_field_name='tag',
                                    translated=True,
                                    search_path='tags',
                                    query_field='tags'
                                    )

    q = search_fields.MultiMatchField(query_fields=['title^4', 'notes^2'],
                                      nested_query_fields={'datasets': ['title', ]})
    sort = search_fields.SortField(
        sort_fields={
            'id': 'id',
            'title': 'title.{lang}.sort',
            'modified': 'modified',
            'created': 'created'
        },
        doc_template='docs/generic/fields/sort_field.html',
        doc_base_url='/institutions',
        doc_field_name='sort'
    )

    facet = search_fields.FacetField(ApplicationAggs)

    class Meta:
        strict = True
        ordered = True


class ApplicationApiRequest(CommonSchema):
    id = search_fields.NumberField(
        _in='path', description='Application ID', example='447', required=True
    )

    class Meta:
        strict = True
        ordered = True


class ExternalResourceSchema(ExtSchema):
    title = core_fields.Str(required=False)
    url = core_fields.Url(required=False)


class CreateSubmissionAttrs(ObjectAttrs):
    applicant_email = core_fields.Email(required=False, default=None)
    author = core_fields.Str(required=False, default=None)
    title = core_fields.Str(required=True, faker_type='application title', example='Some App')
    url = core_fields.Url(required=True)
    notes = core_fields.Str(required=True)
    image = core_fields.Base64String(required=False, default=None, max_size=settings.IMAGE_UPLOAD_MAX_SIZE)
    datasets = core_fields.List(core_fields.Int(), required=False, default=[])
    external_datasets = core_fields.Nested(ExternalResourceSchema, required=False, default={}, many=True)
    keywords = core_fields.List(core_fields.Str(), default='', required=False)
    comment = core_fields.String(required=False, description='Comment body', example='Looks unpretty', default='')

    class Meta:
        strict = True
        ordered = True
        object_type = 'application-submission'


class CreateSubmissionRequest(TopLevel):
    class Meta:
        attrs_schema = CreateSubmissionAttrs
