from django.utils.translation import get_language
from elasticsearch_dsl.query import Term

from mcod.core.api.schemas import (
    CommonSchema,
    ExtSchema,
    ListingSchema,
    NumberTermSchema,
    StringMatchSchema,
    StringTermSchema,
)
from mcod.core.api.search import fields as search_fields


class CategoryFilterSchema(ExtSchema):
    id = search_fields.FilterField(NumberTermSchema, search_path='category', nested_search=True,
                                   query_field='category.id')

    class Meta:
        default_field = 'term'


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
            'by_category': {
                'field': 'category.id',
                'nested_path': 'category',
                'size': 100
            },
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


class ArticleApiSearchRequest(ListingSchema):
    id = search_fields.FilterField(NumberTermSchema,
                                   doc_template='docs/generic/fields/number_term_field.html',
                                   doc_base_url='/articles',
                                   doc_field_name='ID'
                                   )
    title = search_fields.FilterField(StringMatchSchema,
                                      doc_template='docs/generic/fields/string_match_field.html',
                                      doc_base_url='/articles',
                                      doc_field_name='title',
                                      translated=True,
                                      search_path='title'
                                      )
    notes = search_fields.FilterField(StringMatchSchema,
                                      doc_template='docs/generic/fields/string_match_field.html',
                                      doc_base_url='/articles',
                                      doc_field_name='notes',
                                      translated=True,
                                      search_path='notes'
                                      )
    author = search_fields.FilterField(StringMatchSchema,
                                       doc_template='docs/generic/fields/string_match_field.html',
                                       doc_base_url='/articles',
                                       doc_field_name='author',
                                       translated=True,
                                       search_path='author'
                                       )
    category = search_fields.FilterField(CategoryFilterSchema)
    tag = search_fields.FilterField(StringTermSchema,
                                    doc_template='docs/generic/fields/string_term_field.html',
                                    doc_base_url='/articles',
                                    doc_field_name='tag',
                                    translated=True,
                                    search_path='tags',
                                    query_field='tags'
                                    )
    keyword = search_fields.FilterField(StringTermSchema,
                                        doc_template='docs/generic/fields/string_term_field.html',
                                        doc_base_url='/articles',
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
        },
        doc_base_url='/articles',
    )

    facet = search_fields.FacetField(ApplicationAggs)

    class Meta:
        strict = True
        ordered = True


class ArticleApiRequest(CommonSchema):
    id = search_fields.NumberField(
        _in='path', description='Article ID', example='447', required=True
    )

    class Meta:
        strict = True
        ordered = True
