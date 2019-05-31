from django.utils.translation import gettext as _
from marshmallow import validates, ValidationError

from mcod.core.api import fields as core_fields
from mcod.core.api.jsonapi.deserializers import TopLevel, ObjectAttrs
from mcod.core.api.schemas import ListingSchema, CommonSchema, ExtSchema
from mcod.core.api.schemas import NumberTermSchema, StringTermSchema, StringMatchSchema
from mcod.core.api.search import fields as search_fields


class CategoryFilterSchema(ExtSchema):
    id = search_fields.FilterField(NumberTermSchema, search_path='category', nested_search=True,
                                   query_field='category.id')

    class Meta:
        default_field = 'term'


class InstitutionFilterSchema(ExtSchema):
    id = search_fields.FilterField(NumberTermSchema, search_path='institution', nested_search=True,
                                   query_field='institution.id')

    class Meta:
        default_field = 'term'


class ResourceFilterSchema(ExtSchema):
    id = search_fields.FilterField(NumberTermSchema, search_path='resource', nested_search=True,
                                   query_field='resource.id')
    title = search_fields.FilterField(StringMatchSchema, search_path='resource', nested_search=True,
                                      query_field='resource.title')

    class Meta:
        strict = True


class DatasetAggregations(ExtSchema):
    term = search_fields.TermsAggregationField(
        aggs={
            'by_institution': {
                'field': 'institution.id',
                'size': 500,
                'nested_path': 'institution',
            },
            'by_tag': {
                'size': 500,
                'field': 'tags.pl',
                'nested_path': 'tags'
            },
            'by_format': {
                'size': 500,
                'field': 'formats'
            },
            'by_openness_score': {
                'size': 500,
                'field': 'openness_scores'
            },
            'by_category': {
                'field': 'category.id',
                'size': 500,
                'nested_path': 'category'
            }

        }
    )
    # date_histogram = search_fields.DateHistogramAggregationField(
    #     fields = {
    #         'created'
    #     }
    # )


class DatasetApiSearchRequest(ListingSchema):
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
    category = search_fields.FilterField(CategoryFilterSchema)
    institution = search_fields.FilterField(InstitutionFilterSchema)
    tag = search_fields.FilterField(StringTermSchema,
                                    doc_template='docs/generic/fields/string_term_field.html',
                                    doc_base_url='/datasets',
                                    doc_field_name='tag',
                                    translated=True,
                                    search_path='tags',
                                    query_field='tags'
                                    )
    format = search_fields.FilterField(StringTermSchema,
                                       doc_template='docs/generic/fields/string_term_field.html',
                                       doc_base_url='/datasets',
                                       doc_field_name='format',
                                       query_field='formats'
                                       )
    openness_score = search_fields.FilterField(NumberTermSchema,
                                               doc_template='docs/generic/fields/number_term_field.html',
                                               doc_base_url='/datasets',
                                               doc_field_name='openness score'
                                               )
    resource = search_fields.FilterField(ResourceFilterSchema)

    q = search_fields.MultiMatchField(query_fields=['title^4', 'notes^2'],
                                      nested_query_fields={'resources': ['title', ]})
    sort = search_fields.SortField(
        sort_fields={
            'id': 'id',
            'title': 'title.{lang}.sort',
            'modified': 'modified',
            'created': 'created',
            'verified': 'verified',
        },
        doc_template='docs/generic/fields/sort_field.html',
        doc_base_url='/institutions',
        doc_field_name='sort'
    )

    facet = search_fields.FacetField(DatasetAggregations)

    class Meta:
        strict = True
        ordered = True


class DatasetApiRequest(CommonSchema):
    id = search_fields.NumberField(
        _in='path', description='Dataset ID', example='447', required=True
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
