from django.apps import apps
from django_elasticsearch_dsl import DocType, Index, fields

from mcod import settings
from mcod.datasets.documents import datasets_field
from mcod.lib.search.fields import TranslatedTextField, TranslatedKeywordField, TranslatedKeywordsList

Article = apps.get_model('articles', 'Article')
ArticleCategory = apps.get_model('articles', 'ArticleCategory')
Dataset = apps.get_model('datasets', 'Dataset')
Tag = apps.get_model('tags', 'Tag')

INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES['articles'])
INDEX.settings(**settings.ELASTICSEARCH_DSL_INDEX_SETTINGS)


def article_category_field(**kwargs):
    return fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': TranslatedKeywordField('name'),
        'description': TranslatedTextField('description')
    }, **kwargs)


@INDEX.doc_type
class ArticleDoc(DocType):
    id = fields.IntegerField()
    slug = TranslatedKeywordField('slug')
    # FIXME jeden obiekt fields.CompletionField() dla wielu pól podrzędnych?
    title = TranslatedTextField('title', common_params={'suggest': fields.CompletionField()})
    notes = TranslatedTextField('notes', common_params={'raw': fields.TextField()}, std_params=False)

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
    views_count = fields.IntegerField()
    users_following = fields.KeywordField(attr='users_following_list', multi=True)
    status = fields.TextField()
    modified = fields.DateField()
    created = fields.DateField()

    class Meta:
        doc_type = 'article'
        model = Article

    def get_queryset(self):
        return self._doc_type.model.objects.filter(status__in=['published', 'draft'])
