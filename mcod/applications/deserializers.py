from elasticsearch_dsl.query import Term
from marshmallow import pre_load, validates, ValidationError
from django.utils.translation import gettext_lazy as _, get_language

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

    terms = search_fields.TermsAggregationField(
        aggs={
            'by_tag': {
                'field': 'tags',
                'nested_path': 'tags',
                'size': 500,
                'translated': True
            },
            'by_keyword': {
                'field': 'keywords.name',
                'filter': {'keywords.language': get_language},
                'nested_path': 'keywords',
                'size': 500,
            },
        }
    )


class ApplicationApiSearchRequest(ListingSchema):
    id = search_fields.FilterField(NumberTermSchema,
                                   doc_template='docs/generic/fields/number_term_field.html',
                                   doc_base_url='/applications',
                                   doc_field_name='ID'
                                   )
    title = search_fields.FilterField(StringMatchSchema,
                                      doc_template='docs/generic/fields/string_match_field.html',
                                      doc_base_url='/applications',
                                      doc_field_name='title',
                                      translated=True,
                                      search_path='title'
                                      )
    notes = search_fields.FilterField(StringMatchSchema,
                                      doc_template='docs/generic/fields/string_match_field.html',
                                      doc_base_url='/applications',
                                      doc_field_name='notes',
                                      translated=True,
                                      search_path='notes'
                                      )
    has_image_thumb = search_fields.TermsField()

    tag = search_fields.FilterField(StringTermSchema,
                                    doc_template='docs/generic/fields/string_term_field.html',
                                    doc_base_url='/applications',
                                    doc_field_name='tag',
                                    translated=True,
                                    search_path='tags',
                                    query_field='tags'
                                    )

    keyword = search_fields.FilterField(StringTermSchema,
                                        doc_template='docs/generic/fields/string_term_field.html',
                                        doc_base_url='/applications',
                                        doc_field_name='keyword',
                                        search_path='keywords',
                                        query_field='keywords.name',
                                        condition=Term(keywords__language=get_language),
                                        nested_search=True,
                                        )

    q = search_fields.MultiMatchField(query_fields={'title': ['title^4'], 'notes': ['notes^2']},
                                      nested_query_fields={'datasets': ['title', ]})
    sort = search_fields.SortField(
        sort_fields={
            'id': 'id',
            'title': 'title.{lang}.sort',
            'modified': 'modified',
            'created': 'created',
            'views_count': 'views_count',
            'main_page_position': 'main_page_position',
        },
        doc_base_url='/applications',
    )

    facet = search_fields.FacetField(ApplicationAggs)
    is_featured = search_fields.ExistsField("main_page_position")

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
    illustrative_graphics = core_fields.Base64String(
        required=False, default=None, max_size=settings.IMAGE_UPLOAD_MAX_SIZE)
    image_alt = core_fields.Str(required=False, default=None)
    datasets = core_fields.List(core_fields.Str(), required=False, default=[])
    external_datasets = core_fields.Nested(ExternalResourceSchema, required=False, default={}, many=True)
    keywords = core_fields.List(core_fields.Str(), default='', required=False)
    comment = core_fields.String(required=False, description='Comment body', example='Looks unpretty', default='')
    is_personal_data_processing_accepted = core_fields.Boolean(required=True)
    is_terms_of_service_accepted = core_fields.Boolean(required=True)

    class Meta:
        strict = True
        ordered = True
        object_type = 'application-submission'

    @pre_load
    def prepare_data(self, data, **kwargs):
        data['datasets'] = [x.replace('dataset-', '') for x in data.get('datasets', []) if x]
        return data

    @validates('is_personal_data_processing_accepted')
    def validate_is_personal_data_processing_accepted(self, value):
        if not value:
            raise ValidationError(_('This field is required'))

    @validates('is_terms_of_service_accepted')
    def validate_is_terms_of_service_accepted(self, value):
        if not value:
            raise ValidationError(_('This field is required'))


class CreateSubmissionRequest(TopLevel):
    class Meta:
        attrs_schema = CreateSubmissionAttrs
        attrs_schema_required = True
