import marshmallow as ma

from mcod.datasets.depricated.serializers import DatasetSchema
from mcod.lib.fields import OldRelationship
from mcod.lib.serializers import BasicSerializer, ArgsListToDict, SearchMeta, BucketItem, TranslatedStr, \
    TranslatedTagsList


class Aggregations(ArgsListToDict):
    by_modified = ma.fields.Nested(BucketItem(), many=True, attribute='_filter_modified.modified.buckets')
    by_tag = ma.fields.Nested(BucketItem(), many=True, attribute='_filter_tags.tags.buckets')


class ArticlesMeta(SearchMeta):
    aggs = ma.fields.Nested(Aggregations, attribute='aggregations')


class ArticleLicense(ma.Schema):
    id = ma.fields.Int()
    name = ma.fields.Str()
    title = ma.fields.Str()
    url = ma.fields.Str()


class ArticleCategory(ma.Schema):
    id = ma.fields.Int()
    name = TranslatedStr()
    description = TranslatedStr()


class ArticlesSerializer(BasicSerializer):
    id = ma.fields.Int(dump_only=True)
    slug = TranslatedStr()
    title = TranslatedStr()
    notes = TranslatedStr()
    author = ma.fields.Str()
    datasets = OldRelationship(
        related_url='/articles/{article_id},{article_slug}/datasets',
        related_url_kwargs={'article_id': '<id>', 'article_slug': '<slug>'},
        schema=DatasetSchema,
        many=True,
        type_='dataset'
    )
    tags = TranslatedTagsList(ma.fields.String)
    views_count = ma.fields.Integer()
    followed = ma.fields.Boolean()

    modified = ma.fields.Str()
    created = ma.fields.Str()
    license = ma.fields.Nested(ArticleLicense, many=False)
    category = ma.fields.Nested(ArticleCategory, many=False)

    class Meta:
        type_ = "articles"
        self_url_many = "/articles"
        self_url = '/articles/{article_id},{article_slug}'
        self_url_kwargs = {"article_id": "<id>", "article_slug": "<slug>"}
