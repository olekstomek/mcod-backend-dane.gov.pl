from mcod.core.api import fields
from mcod.core.api.jsonapi.serializers import (
    Aggregation,
    ExtAggregation,
    HighlightObjectMixin,
    ObjectAttrs,
    Relationship,
    Relationships,
    TopLevel,
)
from mcod.core.api.schemas import ExtSchema
from mcod.lib.serializers import KeywordsList, TranslatedStr
from mcod.watchers.serializers import SubscriptionMixin


class ArticleApiRelationships(Relationships):
    datasets = fields.Nested(
        Relationship, many=False, default=[], _type='dataset', url_template='{object_url}/datasets', required=True)
    subscription = fields.Nested(Relationship, many=False, _type='subscription',
                                 url_template='{api_url}/auth/subscriptions/{ident}')

    def filter_data(self, data, **kwargs):
        if not self.context.get('is_listing', False) and 'datasets' in data:
            data['datasets'] = data['datasets'].filter(status='published')
        return data


class CategoryAggregation(ExtAggregation):
    class Meta:
        model = 'categories.Category'
        title_field = 'title_i18n'


class ArticleApiAggs(ExtSchema):
    by_created = fields.Nested(Aggregation,
                               many=True,
                               attribute='_filter_by_created.by_created.buckets',
                               )
    by_modified = fields.Nested(Aggregation,
                                many=True,
                                attribute='_filter_by_modified.by_modified.buckets',
                                )
    by_category = fields.Nested(CategoryAggregation,
                                many=True,
                                attribute='_filter_by_category.by_category.inner.buckets'
                                )
    by_tag = fields.Nested(Aggregation,
                           many=True,
                           attribute='_filter_by_tag.by_tag.inner.buckets'
                           )
    by_keyword = fields.Nested(Aggregation,
                               many=True,
                               attribute='_filter_by_keyword.by_keyword.inner.inner.buckets'
                               )


class ArticleLicense(ExtSchema):
    id = fields.String()
    name = fields.String()
    title = fields.String()
    url = fields.String()


class ArticleCategory(ExtSchema):
    id = fields.String()
    name = TranslatedStr()
    description = TranslatedStr()


class ArticleApiAttrs(ObjectAttrs, HighlightObjectMixin):
    slug = TranslatedStr()
    title = TranslatedStr()
    notes = TranslatedStr()
    author = fields.Str(faker_type='firstname')
    keywords = KeywordsList(TranslatedStr(), faker_type='tagslist')
    views_count = fields.Integer(faker_type='integer')
    followed = fields.Boolean()
    modified = fields.Str(faker_type='datetime')
    created = fields.Str(faker_type='datetime')
    license = fields.Nested(ArticleLicense, many=False)
    category = fields.Nested(ArticleCategory, many=False)

    class Meta:
        relationships_schema = ArticleApiRelationships
        object_type = 'article'
        url_template = '{api_url}/articles/{ident}'
        model = 'articles.Article'


class ArticleApiResponse(SubscriptionMixin, TopLevel):
    class Meta:
        attrs_schema = ArticleApiAttrs
        aggs_schema = ArticleApiAggs
