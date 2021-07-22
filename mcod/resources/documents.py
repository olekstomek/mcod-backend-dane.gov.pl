from django.apps import apps
from django_elasticsearch_dsl import fields

from mcod import settings as mcs
from mcod.core.db.elastic import Document
from mcod.lib.search.fields import TranslatedTextField, TranslatedSuggestField
from mcod.watchers.models import ModelWatcher
from mcod.search.documents import SearchDoc, ExtendedDocument
from mcod.search.utils import register_legacy_document, register_unified_document, get_active_document
from mcod.core.api.search.analyzers import lang_synonyms_analyzers, lang_exact_analyzers
from datetime import datetime, time
from mcod.harvester.models import FREQUENCY_CHOICES
from mcod.core.utils import lazy_proxy_to_es_translated_field

Resource = apps.get_model('resources', 'Resource')
Dataset = apps.get_model('datasets', 'Dataset')
TaskResult = apps.get_model('django_celery_results', "TaskResult")
SpecialSign = apps.get_model('special_signs', 'SpecialSign')


@register_unified_document
class ResourceDocument(ExtendedDocument):
    NOTES_FIELD_NAME = 'description'
    # ResourcesSearchDoc
    format = fields.TextField()
    formats = fields.KeywordField(multi=True)
    openness_score = fields.IntegerField()
    openness_scores = fields.IntegerField(multi=True)
    media_type = fields.TextField()
    downloads_count = fields.IntegerField()
    data_date = fields.DateField()
    file_url = fields.TextField()
    download_url = fields.TextField()
    link = fields.TextField()
    file_size = fields.IntegerField()
    types = fields.KeywordField(multi=True)
    dataset = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'title': TranslatedTextField('title'),
        'slug': TranslatedTextField('slug')
    })
    institution = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'title': TranslatedTextField('title'),
        'slug': TranslatedTextField('slug')
    })
    source = fields.NestedField(
        properties={
            'title': fields.TextField(),
            'source_type': fields.TextField(),
            'url': fields.TextField(),
            'update_frequency': TranslatedTextField('update_frequency'),
            'last_import_timestamp': fields.DateField(),
        }
    )

    # ResourceDoc
    id = fields.IntegerField()
    uuid = fields.TextField()
    description = TranslatedTextField('description')
    csv_file_url = fields.TextField()
    csv_file_size = fields.LongField()
    csv_download_url = fields.TextField()
    type = fields.KeywordField()

    geo_data = fields.NestedField(properties={
        'id': fields.IntegerField(),
    })
    tabular_data = fields.NestedField(properties={
        'id': fields.IntegerField(),
    })
    chartable = fields.NestedField(properties={
        'id': fields.IntegerField(),
    })
    data_special_signs = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'symbol': fields.KeywordField(),
            'name': TranslatedTextField('name'),
            'description': TranslatedTextField('description')
        }
    )
    is_chart_creation_blocked = fields.BooleanField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['resources']
        settings = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_SETTINGS
        aliases = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_ALIAS

    class Django:
        model = Resource
        related_models = [Dataset, SpecialSign]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.resources.filter(status='published')
        elif isinstance(related_instance, SpecialSign):
            return related_instance.special_signs_resources.filter(status='published')

    def prepare_model_name(self, instance):
        return instance.category.type

    def prepare_formats(self, instance):
        return [instance.format]

    def prepare_openness_scores(self, instance):
        return [instance.openness_score]

    def prepare_source(self, instance):
        if not instance.dataset.source:
            return {}
        update_frq_text_val = next(freq[1] for freq in FREQUENCY_CHOICES if freq[0] == instance.dataset.source.frequency_in_days)
        return {
            'source_type': instance.dataset.source.source_type,
            'url': instance.dataset.source.url,
            'title': instance.dataset.source.title,
            'last_import_timestamp': instance.dataset.source.last_import_timestamp,
            'update_frequency': lazy_proxy_to_es_translated_field(update_frq_text_val),
        }


@register_legacy_document
class ResourceDoc(Document):
    id = fields.IntegerField()
    slug = fields.TextField()
    uuid = fields.TextField()
    title = TranslatedSuggestField('title')
    description = TranslatedTextField('description')
    notes = TranslatedTextField('description')
    file_url = fields.TextField(attr='file_url')
    file_size = fields.LongField()
    csv_file_url = fields.TextField()
    csv_file_size = fields.LongField()
    csv_download_url = fields.TextField()
    download_url = fields.TextField(attr='download_url')
    link = fields.TextField()
    format = fields.KeywordField()
    type = fields.KeywordField()
    visualization_types = fields.KeywordField(multi=True)
    openness_score = fields.IntegerField()
    is_chart_creation_blocked = fields.BooleanField()

    dataset = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'title': TranslatedTextField('title'),
        'slug': TranslatedTextField('slug')
    })
    institution = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'title': TranslatedTextField('title'),
        'slug': TranslatedTextField('slug')
    })
    geo_data = fields.NestedField(properties={
        'id': fields.IntegerField(),
    })
    tabular_data = fields.NestedField(properties={
        'id': fields.IntegerField(),
    })
    chartable = fields.NestedField(properties={
        'id': fields.IntegerField(),
    })
    data_special_signs = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'symbol': fields.KeywordField(),
            'name': TranslatedTextField('name'),
            'description': TranslatedTextField('description')
        }
    )
    subscriptions = fields.NestedField(
        properties={
            'user_id': fields.IntegerField(),
            'subscription_id': fields.IntegerField()
        }
    )
    views_count = fields.IntegerField()
    downloads_count = fields.IntegerField()

    status = fields.TextField()
    modified = fields.DateField()
    created = fields.DateField()
    verified = fields.DateField()
    data_date = fields.DateField()
    search_type = fields.KeywordField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['resources']
        settings = mcs.ELASTICSEARCH_DSL_INDEX_SETTINGS

    class Django:
        model = Resource
        related_models = [Dataset, SpecialSign]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.resources.filter(status='published')
        elif isinstance(related_instance, SpecialSign):
            return related_instance.special_signs_resources.filter(status='published')

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
class ResourcesSearchDoc(SearchDoc):
    notes = TranslatedTextField('description', raw_field_cls=fields.Text)
    notes_synonyms = TranslatedTextField('notes_synonyms',
                                         attr='description',
                                         analyzers=lang_synonyms_analyzers,
                                         properties=dict())
    notes_exact = TranslatedTextField('notes_exact',
                                      attr='description',
                                      properties=dict(),
                                      analyzers=lang_exact_analyzers)
    format = fields.TextField()
    media_type = fields.TextField()
    downloads_count = fields.IntegerField()
    openness_score = fields.IntegerField()
    data_date = fields.DateField()
    file_url = fields.TextField()
    download_url = fields.TextField()
    link = fields.TextField()
    file_size = fields.IntegerField()
    formats = fields.KeywordField(attr='formats', multi=True)
    types = fields.KeywordField(attr='types', multi=True)
    dataset = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'title': TranslatedTextField('title'),
        'slug': TranslatedTextField('slug')
    })
    institution = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'title': TranslatedTextField('title'),
        'slug': TranslatedTextField('slug')
    })
    visualization_types = fields.KeywordField(multi=True)
    openness_scores = fields.IntegerField(multi=True)
    subscriptions = fields.NestedField(
        properties={
            'user_id': fields.IntegerField(),
            'subscription_id': fields.IntegerField()
        }
    )
    source = fields.NestedField(
        properties={
            'title': fields.TextField(),
            'source_type': fields.TextField(),
            'url': fields.TextField(),
            'update_frequency': TranslatedTextField('update_frequency'),
            'last_import_timestamp': fields.DateField(),
        }
    )
    verified = fields.DateField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['common']
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'max_result_window': 25000
        }

    class Django:
        model = Resource
        related_models = [Dataset, ]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.resources.filter(status='published')

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

    def prepare_formats(self, instance):
        return [instance.format]

    def prepare_search_date(self, instance):
        return datetime.combine(instance.data_date, time(12)) if instance.data_date else instance.created

    def prepare_model_name(self, instance):
        return instance.category.type

    def prepare_visualization_types(self, instance):
        visualization_types = instance.visualization_types
        return visualization_types if visualization_types else ['none']

    def prepare_openness_scores(self, instance):
        return [instance.openness_score, ]

    def prepare_source(self, instance):
        if not instance.dataset.source:
            return {}
        update_frq_text_val = next(freq[1]
                                   for freq in FREQUENCY_CHOICES
                                   if freq[0] == instance.dataset.source.frequency_in_days)
        return {
            'source_type': instance.dataset.source.source_type,
            'url': instance.dataset.source.url,
            'title': instance.dataset.source.title,
            'last_import_timestamp': instance.dataset.source.last_import_timestamp,
            'update_frequency': lazy_proxy_to_es_translated_field(update_frq_text_val),
        }


ResourceDocumentActive = get_active_document(unified_document=ResourceDocument, legacy_document=ResourceDoc)
