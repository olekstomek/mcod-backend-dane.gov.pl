from django.utils.translation import gettext as _
from marshmallow import validates, ValidationError

from mcod.core.api import fields as core_fields
from mcod.core.api.jsonapi.deserializers import TopLevel, ObjectAttrs
from mcod.core.api.schemas import ListingSchema, CommonSchema, ExtSchema
from mcod.core.api.schemas import NumberTermSchema, StringTermSchema, StringMatchSchema
from mcod.core.api.search import fields as search_fields


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
    term = search_fields.TermsAggregationField(
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
        doc_template='docs/generic/fields/string_term_field.html',
        doc_base_url='/resources',
        doc_field_name='media type'
    )
    openness_score = search_fields.FilterField(NumberTermSchema,
                                               doc_template='docs/resources/fields/openness_score.html',
                                               doc_base_url='/resources',
                                               doc_field_name='openness score'
                                               )
    q = search_fields.MultiMatchField(
        query_fields=['title^4', 'description^2'],
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
        },
        doc_template='docs/generic/fields/sort_field.html',
        doc_base_url='/resources',
        doc_field_name='sort'
    )
    dataset = search_fields.FilterField(ResourceDatasetFilterField,
                                        doc_template='docs/resources/fields/dataset.html',
                                        doc_base_url='/resources',
                                        doc_field_name='dataset'
                                        )
    facet = search_fields.FacetField(ResourceAggregations)

    class Meta:
        strict = True
        ordered = True


class ResourceApiRequest(CommonSchema):
    id = search_fields.NumberField(
        _in='path', description='Resource ID', example='447', required=True
    )

    class Meta:
        strict = True
        ordered = True


class TableApiSearchRequest(ListingSchema):
    q = search_fields.QueryStringField(all_fields=True, required=False,
                                       doc_template='docs/tables/fields/query_string.html')

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
