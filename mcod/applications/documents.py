from django.apps import apps
from django_elasticsearch_dsl import DocType, Index, fields

from mcod import settings
from mcod.datasets.documents import datasets_field
from mcod.lib.search.fields import TranslatedTextField, TranslatedKeywordField, TranslatedKeywordsList

Application = apps.get_model('applications', 'Application')
Dataset = apps.get_model('datasets', 'Dataset')
Tag = apps.get_model('tags', 'Tag')

INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES['applications'])
INDEX.settings(**settings.ELASTICSEARCH_DSL_INDEX_SETTINGS)


@INDEX.doc_type
class ApplicationsDoc(DocType):
    id = fields.IntegerField()
    slug = TranslatedKeywordField('slug')
    title = TranslatedTextField('title', common_params={'suggest': fields.CompletionField()})
    notes = TranslatedTextField('notes')

    author = fields.KeywordField()

    url = fields.KeywordField()

    image_url = fields.KeywordField(attr='image_url')
    image_thumb_url = fields.KeywordField(attr='image_thumb_url')

    datasets = datasets_field(attr='published_datasets')
    users_following = fields.KeywordField(attr='users_following_list', multi=True)

    tags = TranslatedKeywordsList(attr='tags_list')

    views_count = fields.IntegerField()
    status = fields.KeywordField()
    modified = fields.DateField()
    created = fields.DateField()

    class Meta:
        doc_type = 'application'
        model = Application

    def get_queryset(self):
        return self._doc_type.model.objects.filter(status='published')
