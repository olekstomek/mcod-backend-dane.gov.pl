from django.apps import apps
from django_elasticsearch_dsl import fields

from mcod import settings as mcs
from mcod.core.db.elastic import Document
from mcod.datasets.documents import datasets_field
from mcod.lib.search.fields import TranslatedTextField, TranslatedSuggestField, TranslatedKeywordField, TranslatedKeywordsList
from mcod.search.documents import SearchDoc, ExtendedDocument
from mcod.search.utils import register_legacy_document, register_unified_document, get_active_document

Application = apps.get_model('applications', 'Application')
Dataset = apps.get_model('datasets', 'Dataset')
Tag = apps.get_model('tags', 'Tag')


@register_unified_document
class ApplicationDocument(ExtendedDocument):
    # ApplicationSearchDoc
    image_alt = TranslatedTextField('image_alt')
    has_image_thumb = fields.BooleanField()
    url = fields.KeywordField()
    illustrative_graphics_url = fields.KeywordField()
    illustrative_graphics_alt = TranslatedTextField('illustrative_graphics_alt')
    image_url = fields.TextField()
    image_thumb_url = fields.KeywordField()
    author = fields.KeywordField()

    # ApplicationsDoc
    id = fields.IntegerField()
    datasets = datasets_field(attr='published_datasets')
    external_datasets = fields.NestedField(
        properties={
            'title': fields.KeywordField(),
            'url': fields.KeywordField(),
        }
    )
    main_page_position = fields.IntegerField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['applications']
        settings = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_SETTINGS
        aliases = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_ALIAS

    class Django:
        model = Application


@register_legacy_document
class ApplicationsDoc(Document):
    id = fields.IntegerField()
    slug = TranslatedKeywordField('slug')
    title = TranslatedSuggestField('title')
    notes = TranslatedTextField('notes')

    author = fields.KeywordField()

    url = fields.KeywordField()

    image_url = fields.KeywordField(attr='image_url')
    image_thumb_url = fields.KeywordField(attr='image_thumb_url')
    image_alt = TranslatedTextField('image_alt')
    illustrative_graphics_url = fields.KeywordField()
    illustrative_graphics_alt = TranslatedTextField('illustrative_graphics_alt')

    datasets = datasets_field(attr='published_datasets')
    external_datasets = fields.NestedField(
        properties={
            'title': fields.KeywordField(),
            'url': fields.KeywordField(),
        }
    )
    tags = TranslatedKeywordsList(attr='tags_list')
    keywords = fields.NestedField(attr='keywords_list',
                                  properties={
                                      'name': fields.KeywordField(),
                                      'language': fields.KeywordField(),
                                  })

    views_count = fields.IntegerField()
    status = fields.KeywordField()
    modified = fields.DateField()
    created = fields.DateField()
    search_type = fields.KeywordField()
    has_image_thumb = fields.BooleanField()
    main_page_position = fields.IntegerField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['applications']
        settings = mcs.ELASTICSEARCH_DSL_INDEX_SETTINGS

    class Django:
        model = Application

    def get_queryset(self):
        return super().get_queryset().filter(status='published')


@register_legacy_document
class ApplicationSearchDoc(SearchDoc):
    image_alt = TranslatedTextField('image_alt')
    tags = TranslatedKeywordsList(attr='tags_list')
    keywords = fields.NestedField(attr='keywords_list',
                                  properties={
                                      'name': fields.KeywordField(),
                                      'language': fields.KeywordField(),
                                  })

    has_image_thumb = fields.BooleanField()

    url = fields.url = fields.KeywordField()
    illustrative_graphics_url = fields.KeywordField()
    illustrative_graphics_alt = TranslatedTextField('illustrative_graphics_alt')
    image_url = fields.TextField()
    image_thumb_url = fields.KeywordField()
    author = fields.KeywordField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['common']
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'max_result_window': 25000
        }

    class Django:
        model = Application

    def get_queryset(self):
        return super().get_queryset().filter(status='published')


ApplicationDocumentActive = get_active_document(unified_document=ApplicationDocument, legacy_document=ApplicationsDoc)
