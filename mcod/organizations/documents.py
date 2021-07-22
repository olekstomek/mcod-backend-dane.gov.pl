from django.apps import apps
from django_elasticsearch_dsl import fields

from mcod import settings as mcs
from mcod.core.db.elastic import Document
from mcod.datasets.documents import datasets_field
from mcod.lib.search.fields import TranslatedTextField, TranslatedKeywordField, TranslatedSuggestField
from mcod.watchers.models import ModelWatcher
from mcod.search.documents import SearchDoc, ExtendedDocument
from mcod.search.utils import register_legacy_document, register_unified_document, get_active_document
from mcod.core.api.search.analyzers import lang_synonyms_analyzers, lang_exact_analyzers

Organization = apps.get_model('organizations', 'Organization')
Dataset = apps.get_model('datasets', 'Dataset')


@register_unified_document
class InstitutionDocument(ExtendedDocument):
    NOTES_FIELD_NAME = 'description'
    # InstitutionSearchDoc
    image_url = fields.TextField()
    abbreviation = fields.KeywordField()
    postal_code = fields.KeywordField()
    city = fields.KeywordField()
    street_type = fields.KeywordField()
    street = fields.KeywordField()
    street_number = fields.KeywordField()
    flat_number = fields.KeywordField()
    email = fields.KeywordField()
    epuap = fields.KeywordField()
    fax = fields.KeywordField(attr='fax_display')
    tel = fields.KeywordField(attr='phone_display')
    regon = fields.KeywordField()
    website = fields.KeywordField()
    institution_type = fields.KeywordField()
    published_datasets_count = fields.IntegerField()
    published_resources_count = fields.IntegerField()
    sources = fields.NestedField(
        properties={
            'title': fields.TextField(),
            'url': fields.TextField(),
            'source_type': fields.TextField(),
        }
    )

    # InstitutionDoc
    id = fields.IntegerField()
    description = TranslatedTextField('description')
    datasets = datasets_field(attr='published_datasets')

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['institutions']
        settings = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_SETTINGS
        aliases = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_ALIAS

    class Django:
        model = Organization
        related_models = [Dataset, ]

    def prepare_model(self, instance):
        return 'institution'

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.organization


@register_legacy_document
class InstitutionDoc(Document):
    id = fields.IntegerField()
    slug = TranslatedKeywordField('slug')
    title = TranslatedSuggestField('title')
    description = TranslatedTextField('description')
    notes = TranslatedTextField('description')
    image_url = fields.TextField(
        attr='image_url'
    )

    abbreviation = fields.KeywordField()
    postal_code = fields.KeywordField()
    city = fields.KeywordField()
    street_type = fields.KeywordField()
    street = fields.KeywordField()
    street_number = fields.KeywordField()
    flat_number = fields.KeywordField()
    email = fields.KeywordField()
    epuap = fields.KeywordField()
    institution_type = fields.KeywordField()
    regon = fields.KeywordField()
    tel = fields.KeywordField(attr='phone_display')
    fax = fields.KeywordField(attr='fax_display')
    website = fields.KeywordField()
    datasets = datasets_field(attr='published_datasets')
    published_datasets_count = fields.IntegerField()
    published_resources_count = fields.IntegerField()
    sources = fields.NestedField(
        properties={
            'title': fields.TextField(),
            'url': fields.TextField(),
            'source_type': fields.TextField(),
        }
    )
    subscriptions = fields.NestedField(
        properties={
            'user_id': fields.IntegerField(),
            'subscription_id': fields.IntegerField()
        }
    )
    status = fields.TextField()
    modified = fields.DateField()
    created = fields.DateField()
    search_type = fields.KeywordField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['institutions']
        settings = mcs.ELASTICSEARCH_DSL_INDEX_SETTINGS

    class Django:
        model = Organization
        related_models = [Dataset, ]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.organization

    def get_queryset(self):
        return super().get_queryset().filter(status='published')

    def prepare_subscriptions(self, instance):
        try:
            watcher = ModelWatcher.objects.get_from_instance(instance)
            return [
                {'user_id': subscription.user_id, 'subscription_id': subscription.id} for subscription in
                watcher.subscriptions.all()
            ]
        except ModelWatcher.DoesNotExist:
            return []


@register_legacy_document
class InstitutionSearchDoc(SearchDoc):
    notes = TranslatedTextField('description', raw_field_cls=fields.Text)
    notes_synonyms = TranslatedTextField('notes_synonyms',
                                         attr='description',
                                         analyzers=lang_synonyms_analyzers,
                                         properties=dict())
    notes_exact = TranslatedTextField('notes_exact',
                                      attr='description',
                                      properties=dict(),
                                      analyzers=lang_exact_analyzers)
    image_url = fields.TextField(
        attr='image_url'
    )
    abbreviation = fields.KeywordField()
    postal_code = fields.KeywordField()
    city = fields.KeywordField()
    street_type = fields.KeywordField()
    street = fields.KeywordField()
    street_number = fields.KeywordField()
    flat_number = fields.KeywordField()
    email = fields.KeywordField()
    epuap = fields.KeywordField()
    fax = fields.KeywordField(attr='fax_display')
    tel = fields.KeywordField(attr='phone_display')
    regon = fields.KeywordField()
    website = fields.KeywordField()
    institution_type = fields.KeywordField()
    published_datasets_count = fields.IntegerField()
    published_resources_count = fields.IntegerField()
    sources = fields.NestedField(
        properties={
            'title': fields.TextField(),
            'url': fields.TextField(),
            'source_type': fields.TextField(),
        }
    )

    subscriptions = fields.NestedField(
        properties={
            'user_id': fields.IntegerField(),
            'subscription_id': fields.IntegerField()
        }
    )

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['common']
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'max_result_window': 25000
        }

    class Django:
        model = Organization
        related_models = [Dataset, ]

    def get_queryset(self):
        return super().get_queryset().filter(status='published')

    def prepare_subscriptions(self, instance):
        try:
            watcher = ModelWatcher.objects.get_from_instance(instance)
            return [
                {'user_id': subscription.user_id, 'subscription_id': subscription.id} for subscription in
                watcher.subscriptions.all()
            ]
        except ModelWatcher.DoesNotExist:
            return []

    def prepare_model(self, instance):
        return 'institution'

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.organization


InstitutionDocumentActive = get_active_document(unified_document=InstitutionDocument, legacy_document=InstitutionDoc)
