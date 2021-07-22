from django.apps import apps
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from mcod import settings as mcs
from mcod.datasets.documents import datasets_field
from mcod.lib.search.fields import TranslatedTextField
from mcod.search.documents import ExtendedDocument

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


@registry.register_document
class ArticleDocument(ExtendedDocument):
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

    datasets = datasets_field(attr='published_datasets')

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['articles']
        settings = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_SETTINGS
        aliases = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_ALIAS

    class Django:
        model = Article

    def prepare_model(self, instance):
        return instance.category.type
