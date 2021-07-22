from django.utils.translation import gettext as _
from marshmallow import validates, ValidationError

from mcod.core.api import fields as core_fields
from mcod.core.api.jsonapi.deserializers import TopLevel, ObjectAttrs
from mcod.core.api.schemas import (
    CommonSchema, ExtSchema, ListingSchema, ListTermsSchema, NumberTermSchema, StringTermSchema, StringMatchSchema,
    DateTermSchema)
from mcod.core.api.search import fields as search_fields
from mcod.datasets.deserializers import RdfValidationRequest


class ResourceDatasetFilterField(ExtSchema):
    id = search_fields.FilterField(NumberTermSchema,
                                   search_path='dataset',
                                   nested_search=True,
                                   query_field='dataset.id',
                                   )
    title = search_fields.FilterField(StringMatchSchema,
                                      search_path='dataset',
                                      nested_search=True,
                                      query_field='dataset.title')

    class Meta:
        strict = True


class ResourceAggregations(ExtSchema):
    date_histogram = search_fields.DateHistogramAggregationField(
        aggs={
            'by_modified': {
                'field': 'modified',
                'size': 500
            },
            'by_created': {
                'field': 'created',
                'size': 500
            },
            'by_verified': {
                'field': 'verified',
                'size': 500
            }
        }
    )
    terms = search_fields.TermsAggregationField(
        aggs={
            'by_format': {
                'size': 500,
                'field': 'format'
            },
            'by_type': {
                'size': 500,
                'field': 'type',
            },
            'by_openness_score': {
                'size': 500,
                'field': 'openness_score'
            },
            'by_visualization_type': {
                'size': 500,
                'field': 'visualization_types'
            },
        }
    )


class ResourceApiSearchRequest(ListingSchema):
    id = search_fields.FilterField(NumberTermSchema,
                                   doc_template='docs/generic/fields/number_term_field.html',
                                   doc_base_url='/resources',
                                   doc_field_name='ID'
                                   )
    title = search_fields.FilterField(StringMatchSchema,
                                      doc_template='docs/generic/fields/string_match_field.html',
                                      doc_base_url='/resources',
                                      doc_field_name='title',
                                      translated=True,
                                      search_path='title'
                                      )
    description = search_fields.FilterField(StringMatchSchema,
                                            doc_template='docs/generic/fields/string_match_field.html',
                                            doc_base_url='/resources',
                                            doc_field_name='description',
                                            translated=True,
                                            search_path='description'
                                            )
    format = search_fields.FilterField(
        StringTermSchema,
        doc_template='docs/generic/fields/string_term_field.html',
        doc_base_url='/resources',
        doc_field_name='format'
    )
    media_type = search_fields.FilterField(
        StringTermSchema,
        query_field='type',
        doc_template='docs/generic/fields/string_term_field.html',
        doc_base_url='/resources',
        doc_field_name='media type'
    )
    type = search_fields.FilterField(
        StringTermSchema,
        query_field='type',
        doc_template='docs/generic/fields/string_term_field.html',
        doc_base_url='/resources',
        doc_field_name='type'
    )
    visualization_type = search_fields.FilterField(
        ListTermsSchema,
        query_field='visualization_types',
        doc_template='docs/generic/fields/string_term_field.html',
        doc_base_url='/resources',
        doc_field_name='visualization type'
    )
    openness_score = search_fields.FilterField(
        NumberTermSchema,
        doc_template='docs/resources/fields/openness_score.html',
        doc_base_url='/resources',
        doc_field_name='openness score'
    )
    created = search_fields.FilterField(DateTermSchema,
                                        doc_template='docs/generic/fields/number_term_field.html',
                                        doc_base_url='/resources',
                                        doc_field_name='created'
                                        )
    q = search_fields.MultiMatchField(
        query_fields={'title': ['title^4'], 'description': ['description^2']},
        nested_query_fields={'dataset': ['title', ]},
        doc_template='docs/generic/fields/query_field.html',
        doc_base_url='/resources',
        doc_field_name='q'
    )
    sort = search_fields.SortField(
        sort_fields={
            'id': 'id',
            'title': 'title.{lang}.raw',
            'modified': 'modified',
            'created': 'created',
            'verified': 'verified',
            'data_date': 'data_date',
            'views_count': 'views_count',
        },
        doc_base_url='/resources',
    )
    dataset = search_fields.FilterField(ResourceDatasetFilterField,
                                        doc_template='docs/resources/fields/dataset.html',
                                        doc_base_url='/resources',
                                        doc_field_name='dataset'
                                        )
    facet = search_fields.FacetField(ResourceAggregations)
    include = search_fields.StringField(
        data_key='include',
        description='Allow the client to customize which related resources should be returned in included section.',
        allowEmptyValue=True,
    )

    class Meta:
        strict = True
        ordered = True


class ResourceApiRequest(CommonSchema):
    id = search_fields.NumberField(
        _in='path', description='Resource ID', example='447', required=True
    )
    include = search_fields.StringField(
        data_key='include',
        description='Allow the client to customize which related resources should be returned in included section.',
        allowEmptyValue=True, example='dataset',
    )

    class Meta:
        strict = True
        ordered = True


class ResourceRdfApiRequest(ResourceApiRequest, RdfValidationRequest):
    class Meta:
        strict = True
        ordered = True


class TableApiSearchRequest(ListingSchema):
    q = search_fields.QueryStringField(all_fields=True, required=False,
                                       doc_template='docs/tables/fields/query_string.html')
    p = search_fields.TableApiMultiMatchField(
        required=False, description='Search phrase', doc_template='docs/generic/fields/query_field.html')
    sort = search_fields.SortField(
        sort_fields={},
        doc_base_url='/resources',
    )
    sum = search_fields.ColumnMetricAggregationField(aggregation_type='sum')
    avg = search_fields.ColumnMetricAggregationField(aggregation_type='avg')

    class Meta:
        strict = True
        ordered = True


class TableApiRequest(CommonSchema):
    id = search_fields.StringField(
        _in='path', description='Row ID', example='a52c4405-7d0c-5166-bba9-bde651f46fb9', required=True
    )

    class Meta:
        strict = True
        ordered = True


class GeoApiSearchRequest(ListingSchema):
    bbox = search_fields.BBoxField(required=False)
    dist = search_fields.GeoDistanceField(required=False)
    q = search_fields.QueryStringField(
        all_fields=True, required=False, doc_template='docs/tables/fields/query_string.html')
    sort = search_fields.SortField(doc_base_url='/resources')

    no_data = search_fields.NoDataField()

    class Meta:
        strict = True
        ordered = True


class CreateCommentAttrs(ObjectAttrs):
    comment = core_fields.String(required=True, description='Comment body', example='Looks unpretty')

    @validates('comment')
    def validate_comment(self, comment):
        if len(comment) < 3:
            raise ValidationError(_('Comment must be at least 3 characters long'))

    class Meta:
        strict = True
        ordered = True
        object_type = 'comment'


class CreateCommentRequest(TopLevel):
    class Meta:
        attrs_schema = CreateCommentAttrs


class CreateChartAttrs(ObjectAttrs):
    resource_id = core_fields.Int(dump_only=True)
    chart = core_fields.Raw(required=True)
    is_default = core_fields.Bool()

    class Meta:
        object_type = "chart"
        strict = True
        ordered = True


class CreateChartRequest(TopLevel):
    class Meta:
        attrs_schema = CreateChartAttrs
        attrs_schema_required = True
