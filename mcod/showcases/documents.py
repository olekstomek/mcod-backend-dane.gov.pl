from django.apps import apps
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from mcod import settings as mcs
from mcod.datasets.documents import datasets_field
from mcod.lib.search.fields import TranslatedTextField
from mcod.search.documents import ExtendedDocument

Showcase = apps.get_model('showcases.Showcase')
Dataset = apps.get_model('datasets.Dataset')
Tag = apps.get_model('tags.Tag')


@registry.register_document
class ShowcaseDocument(ExtendedDocument):
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

    showcase_category = fields.KeywordField()
    showcase_types = fields.KeywordField(multi=True)
    showcase_platforms = fields.KeywordField(multi=True)
    license_type = fields.KeywordField()
    file_url = fields.KeywordField()
    is_desktop_app = fields.BooleanField()
    is_mobile_app = fields.BooleanField()
    mobile_apple_url = fields.KeywordField()
    mobile_google_url = fields.KeywordField()
    desktop_linux_url = fields.KeywordField()
    desktop_macos_url = fields.KeywordField()
    desktop_windows_url = fields.KeywordField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['showcases']
        settings = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_SETTINGS
        aliases = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_ALIAS

    class Django:
        model = Showcase
