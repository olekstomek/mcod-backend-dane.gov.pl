from django.apps import apps
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from mcod import settings as mcs
from mcod.datasets.documents import datasets_field
from mcod.lib.search.fields import TranslatedTextField
from mcod.search.documents import ExtendedDocument

Application = apps.get_model('applications', 'Application')
Dataset = apps.get_model('datasets', 'Dataset')
Tag = apps.get_model('tags', 'Tag')


@registry.register_document
class ApplicationDocument(ExtendedDocument):
    image_alt = TranslatedTextField('image_alt')
    has_image_thumb = fields.BooleanField()
    url = fields.KeywordField()
    illustrative_graphics_url = fields.KeywordField()
    illustrative_graphics_alt = TranslatedTextField('illustrative_graphics_alt')
    image_url = fields.TextField()
    image_thumb_url = fields.KeywordField()
    author = fields.KeywordField()

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
