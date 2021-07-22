from django.apps import apps
from django_elasticsearch_dsl import fields

from mcod import settings as mcs
from mcod.core.db.elastic import Document
from mcod.datasets.documents import datasets_field
from mcod.lib.search.fields import TranslatedTextField, TranslatedSuggestField, TranslatedKeywordField, TranslatedKeywordsList
from mcod.search.documents import SearchDoc, ExtendedDocument
from mcod.search.utils import register_legacy_document, register_unified_document, get_active_document

Article = apps.get_model('articles', 'Article')
ArticleCategory = apps.get_model('articles', 'ArticleCategory')
Dataset = apps.get_model('datasets', 'Dataset')
Tag = apps.get_model('tags', 'Tag')


def article_category_field(**kwargs):
    return fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'image_url': fields.KeywordField(),
            'title': TranslatedTextField('title', attr='name'),
            'name': TranslatedTextField('name'),
            'description': TranslatedTextField('description')
        }
    )


@register_unified_document
class ArticleDocument(ExtendedDocument):
    # ArticleSearchDoc
    author = fields.KeywordField()
    category = article_category_field()
    license = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
            'title': fields.TextField(),
            'url': fields.TextField()
        }
    )
    html_url = fields.KeywordField(attr='frontend_absolute_url')

    # ArticleDoc
    id = fields.IntegerField()
    datasets = datasets_field(attr='published_datasets')

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['articles']
        settings = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_SETTINGS
        aliases = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_ALIAS

    class Django:
        model = Article

    def prepare_model(self, instance):
        return instance.category.type


@register_legacy_document
class ArticleDoc(Document):
    id = fields.IntegerField()
    slug = TranslatedKeywordField('slug')
    # FIXME jeden obiekt fields.CompletionField() dla wielu pól podrzędnych?
    title = TranslatedSuggestField('title')
    notes = TranslatedTextField('notes', raw_field_cls=fields.TextField)

    author = fields.KeywordField()

    datasets = datasets_field(attr='published_datasets')
    category = article_category_field()
    license = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
            'title': fields.TextField(),
            'url': fields.TextField()
        }
    )

    tags = TranslatedKeywordsList(attr='tags_list')
    keywords = fields.NestedField(attr='keywords_list',
                                  properties={
                                      'name': fields.KeywordField(),
                                      'language': fields.KeywordField(),
                                  })
    views_count = fields.IntegerField()
    status = fields.TextField()
    modified = fields.DateField()
    created = fields.DateField()
    search_type = fields.KeywordField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['articles']
        settings = mcs.ELASTICSEARCH_DSL_INDEX_SETTINGS

    class Django:
        model = Article

    def get_queryset(self):
        return super().get_queryset().filter(status='published')


@register_legacy_document
class ArticleSearchDoc(SearchDoc):
    author = fields.KeywordField()
    category = article_category_field()
    tags = TranslatedKeywordsList(attr='tags_list')
    keywords = fields.NestedField(attr='keywords_list',
                                  properties={
                                      'name': fields.KeywordField(),
                                      'language': fields.KeywordField(),
                                  })
    license = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
            'title': fields.TextField(),
            'url': fields.TextField()
        }
    )
    html_url = fields.KeywordField(attr='frontend_absolute_url')

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['common']
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'max_result_window': 25000
        }

    class Django:
        model = Article

    def get_queryset(self):
        qs = super().get_queryset().filter(status='published', category__type='article')
        # qs.filter(category__type__in=('article', 'knowledge_base'))
        return qs

    def prepare_model(self, instance):
        return instance.category.type


ArticleDocumentActive = get_active_document(unified_document=ArticleDocument, legacy_document=ArticleDoc)
