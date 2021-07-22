from django.apps import apps
from django_elasticsearch_dsl import fields
from mcod import settings as mcs
from mcod.search.documents import SearchDoc, ExtendedDocument
from mcod.search.utils import register_legacy_document, register_unified_document
from mcod.core.api.search.analyzers import lang_synonyms_analyzers, lang_exact_analyzers
from mcod.lib.search.fields import TranslatedTextField

KBPage = apps.get_model('cms', 'KBPage')


@register_unified_document
class KBPageDocument(ExtendedDocument):
    NOTES_FIELD_NAME = 'body'

    html_url = fields.KeywordField(attr='full_url')

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['knowledge_base_pages']
        settings = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_SETTINGS
        aliases = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_ALIAS

    class Django:
        model = KBPage

    def get_queryset(self):
        return KBPage.objects.filter(live=True)

    def prepare_model(self, instance):
        return 'knowledge_base'

    def prepare_search_date(self, instance):
        return instance.last_published_at


@register_legacy_document
class KBPageSearchDoc(SearchDoc):
    notes = TranslatedTextField('notes', attr='body', raw_field_cls=fields.Text)
    notes_synonyms = TranslatedTextField('notes_synonyms',
                                         attr='body',
                                         analyzers=lang_synonyms_analyzers,
                                         properties=dict())
    notes_exact = TranslatedTextField('notes_exact',
                                      attr='body',
                                      properties=dict(),
                                      analyzers=lang_exact_analyzers)

    html_url = fields.KeywordField(attr='full_url')

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['common']
        settings = mcs.ELASTICSEARCH_DSL_INDEX_SETTINGS

    class Django:
        model = KBPage

    def get_queryset(self):
        return super().get_queryset().filter(live=True)

    def prepare_search_date(self, instance):
        return instance.last_published_at

    def prepare_model(self, instance):
        return 'knowledge_base'

    def prepare_id(self, instance):
        return '{}-{}'.format('knowledge_base', instance.pk)
