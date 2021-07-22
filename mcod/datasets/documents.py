from django.apps import apps
from django_elasticsearch_dsl import fields

from mcod import settings as mcs
from mcod.core.db.elastic import Document
from mcod.lib.search.fields import TranslatedTextField, TranslatedSuggestField, TranslatedKeywordField, TranslatedKeywordsList
from mcod.users.models import UserFollowingDataset
from mcod.watchers.models import ModelWatcher
from mcod.core.utils import lazy_proxy_to_es_translated_field
from mcod.harvester.models import FREQUENCY_CHOICES
from mcod.search.documents import SearchDoc, ExtendedDocument
from mcod.search.utils import register_legacy_document, register_unified_document, get_active_document

Dataset = apps.get_model('datasets', 'Dataset')
Organization = apps.get_model('organizations', 'Organization')
Category = apps.get_model('categories', 'Category')
Tag = apps.get_model('tags', 'Tag')
Resource = apps.get_model('resources', 'Resource')
Article = apps.get_model('articles', 'Article')
Application = apps.get_model('applications', 'Application')
DataSource = apps.get_model('harvester', 'DataSource')


def datasets_field(**kwargs):
    return fields.NestedField(properties={
        'id': fields.IntegerField(),
        'title': TranslatedTextField('title'),
        'notes': TranslatedTextField('notes'),
        'category': fields.KeywordField(attr='category.title'),
        'formats': fields.KeywordField(attr='formats', multi=True),
        'downloads_count': fields.IntegerField(attr='downloads_count'),
        'views_count': fields.IntegerField(attr='views_count'),
        'openness_scores': fields.IntegerField(attr='openness_scores'),
        'modified': fields.DateField(),
        'slug': TranslatedKeywordField('slug'),
        'verified': fields.DateField(),
    }, **kwargs)


@register_unified_document
class DatasetDocument(ExtendedDocument):
    # DatasetSearchDoc
    license_chosen = fields.IntegerField()
    license_condition_db_or_copyrighted = fields.TextField()
    license_condition_personal_data = fields.TextField()
    license_condition_modification = fields.BooleanField()
    license_condition_original = fields.BooleanField()
    license_condition_responsibilities = fields.TextField()
    license_condition_source = fields.BooleanField()
    license_condition_timestamp = fields.BooleanField()
    license_name = fields.TextField()
    license_description = fields.TextField()
    resource_modified = fields.DateField(attr='last_modified_resource')
    url = fields.KeywordField()
    source = fields.NestedField(
        properties={
            'title': fields.TextField(),
            'source_type': fields.TextField(),
            'url': fields.TextField(),
            'update_frequency': TranslatedTextField('update_frequency'),
            'last_import_timestamp': fields.DateField(),
        }
    )

    formats = fields.KeywordField(multi=True)
    types = fields.KeywordField(multi=True)
    openness_scores = fields.IntegerField(multi=True)
    institution = fields.NestedField(
        attr='organization',
        properties={
            'id': fields.IntegerField(),
            'title': TranslatedTextField('title'),
            'slug': TranslatedTextField('slug'),
        }
    )
    category = fields.NestedField(
        properties={
            'id': fields.IntegerField(attr='id'),
            'image_url': fields.KeywordField(),
            'title': TranslatedTextField('title'),
            'description': TranslatedTextField('description')
        }
    )
    categories = fields.NestedField(
        properties={
            'id': fields.IntegerField(attr='id'),
            'image_url': fields.KeywordField(),
            'code': fields.KeywordField(),
            'title': TranslatedTextField('title'),
            'description': TranslatedTextField('description')
        }
    )
    downloads_count = fields.IntegerField()
    image_url = fields.TextField()
    image_alt = TranslatedTextField('image_alt')

    # DatasetsDoc
    id = fields.IntegerField()
    version = fields.KeywordField()
    source_title = fields.TextField()
    source_type = fields.TextField()
    source_url = fields.TextField()

    resources = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'title': TranslatedTextField('title')
        }
    )
    applications = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'title': TranslatedTextField('title')
        }
    )

    articles = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'title': TranslatedTextField('title')
        }
    )

    update_frequency = fields.KeywordField()
    users_following = fields.KeywordField(attr='users_following_list', multi=True)
    last_modified_resource = fields.DateField(attr='last_modified_resource')

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['datasets']
        settings = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_SETTINGS
        aliases = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_ALIAS

    class Django:
        model = Dataset
        related_models = [Organization, Category, Application, Article, Resource, UserFollowingDataset, DataSource]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, UserFollowingDataset):
            return related_instance.follower.followed_applications.all()
        if isinstance(related_instance, Application):
            return related_instance.datasets.filter(status='published')
        if isinstance(related_instance, Article):
            return related_instance.datasets.filter(status='published')
        if isinstance(related_instance, Resource):
            return related_instance.dataset
        if isinstance(related_instance, Category):
            return related_instance.dataset_set.filter(status='published')
        if isinstance(related_instance, Organization):
            return related_instance.datasets.filter(status='published')
        if isinstance(related_instance, DataSource):
            return related_instance.datasource_datasets.filter(status='published')

    def prepare_search_date(self, instance):
        return instance.verified

    def prepare_source(self, instance):
        if not instance.source:
            return {}
        update_frq_text_val = next(freq[1] for freq in FREQUENCY_CHOICES if freq[0] == instance.source.frequency_in_days)
        return {
            'source_type': instance.source.source_type,
            'url': instance.source.url,
            'title': instance.source.title,
            'last_import_timestamp': instance.source.last_import_timestamp,
            'update_frequency': lazy_proxy_to_es_translated_field(update_frq_text_val),
        }


@register_legacy_document
class DatasetsDoc(Document):
    id = fields.IntegerField()
    slug = TranslatedKeywordField('slug')
    title = TranslatedSuggestField('title')
    version = fields.KeywordField()
    url = fields.KeywordField()
    notes = TranslatedTextField('notes')
    source_title = fields.TextField()
    source_type = fields.TextField()
    source_url = fields.TextField()

    institution = fields.NestedField(attr='organization',
                                     properties={
                                         'id': fields.IntegerField(),
                                         'title': TranslatedTextField('title'),
                                         'slug': TranslatedTextField('slug'),
                                     })

    category = fields.NestedField(
        attr='category',
        properties={
            'id': fields.IntegerField(attr='id'),
            'image_url': fields.KeywordField(),
            'title': TranslatedTextField('title'),
            'description': TranslatedTextField('description')
        }
    )
    categories = fields.NestedField(
        attr='categories',
        properties={
            'id': fields.IntegerField(attr='id'),
            'image_url': fields.KeywordField(),
            'code': fields.KeywordField(),
            'title': TranslatedTextField('title'),
            'description': TranslatedTextField('description')
        }
    )

    resources = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'title': TranslatedTextField('title')
        }
    )
    applications = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'title': TranslatedTextField('title')
        }
    )

    articles = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'title': TranslatedTextField('title')
        }
    )

    tags = TranslatedKeywordsList(attr='tags_list')
    keywords = fields.NestedField(attr='keywords_list',
                                  properties={
                                      'name': fields.KeywordField(),
                                      'language': fields.KeywordField(),
                                  })
    formats = fields.KeywordField(attr='formats', multi=True)
    types = fields.KeywordField(attr='types', multi=True)
    subscriptions = fields.NestedField(
        properties={
            'user_id': fields.IntegerField(),
            'subscription_id': fields.IntegerField()
        }
    )
    license_chosen = fields.IntegerField()
    license_condition_db_or_copyrighted = fields.TextField()
    license_condition_personal_data = fields.TextField()
    license_condition_modification = fields.BooleanField()
    license_condition_original = fields.BooleanField()
    license_condition_responsibilities = fields.TextField()
    license_condition_source = fields.BooleanField()
    license_condition_timestamp = fields.BooleanField()
    license_name = fields.TextField(attr='license_name')
    license_description = fields.TextField(attr='license_description')
    update_frequency = fields.KeywordField()

    openness_scores = fields.IntegerField(attr='openness_scores', multi=True)
    users_following = fields.KeywordField(attr='users_following_list', multi=True)
    views_count = fields.IntegerField()
    downloads_count = fields.IntegerField()
    status = fields.KeywordField()
    modified = fields.DateField()
    last_modified_resource = fields.DateField(attr='last_modified_resource')
    created = fields.DateField()
    verified = fields.DateField()
    search_type = fields.KeywordField()
    visualization_types = fields.KeywordField(multi=True)
    image_url = fields.KeywordField(attr='image_url')
    image_alt = TranslatedTextField('image_alt')

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['datasets']
        settings = mcs.ELASTICSEARCH_DSL_INDEX_SETTINGS

    class Django:
        model = Dataset
        related_models = [Organization, Category, Application, Article, Resource, UserFollowingDataset, DataSource]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, UserFollowingDataset):
            return related_instance.follower.followed_applications.all()
        if isinstance(related_instance, Application):
            return related_instance.datasets.filter(status='published')
        if isinstance(related_instance, Article):
            return related_instance.datasets.filter(status='published')
        if isinstance(related_instance, Resource):
            return related_instance.dataset
        if isinstance(related_instance, Category):
            return related_instance.dataset_set.filter(status='published')
        if isinstance(related_instance, Organization):
            return related_instance.datasets.filter(status='published')
        if isinstance(related_instance, DataSource):
            return related_instance.datasource_datasets.filter(status='published')

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
class DatasetSearchDoc(SearchDoc):
    license_chosen = fields.IntegerField()
    license_condition_db_or_copyrighted = fields.TextField()
    license_condition_personal_data = fields.TextField()
    license_condition_modification = fields.BooleanField()
    license_condition_original = fields.BooleanField()
    license_condition_responsibilities = fields.TextField()
    license_condition_source = fields.BooleanField()
    license_condition_timestamp = fields.BooleanField()
    license_name = fields.TextField()
    license_description = fields.TextField()
    resource_modified = fields.DateField(attr='last_modified_resource')
    url = fields.KeywordField()
    source = fields.NestedField(
        properties={
            'title': fields.TextField(),
            'source_type': fields.TextField(),
            'url': fields.TextField(),
            'update_frequency': TranslatedTextField('update_frequency'),
            'last_import_timestamp': fields.DateField(),
        }
    )
    tags = TranslatedKeywordsList(attr='tags_list')
    keywords = fields.NestedField(attr='keywords_list',
                                  properties={
                                      'name': fields.KeywordField(),
                                      'language': fields.KeywordField(),
                                  })
    formats = fields.KeywordField(attr='formats', multi=True)
    types = fields.KeywordField(attr='types', multi=True)
    openness_scores = fields.IntegerField(attr='openness_scores', multi=True)
    institution = fields.NestedField(attr='organization',
                                     properties={
                                         'id': fields.IntegerField(),
                                         'title': TranslatedTextField('title'),
                                         'slug': TranslatedTextField('slug'),
                                     })
    category = fields.NestedField(
        attr='category',
        properties={
            'id': fields.IntegerField(attr='id'),
            'image_url': fields.KeywordField(),
            'title': TranslatedTextField('title'),
            'description': TranslatedTextField('description')
        }
    )
    categories = fields.NestedField(
        attr='categories',
        properties={
            'id': fields.IntegerField(attr='id'),
            'image_url': fields.KeywordField(),
            'code': fields.KeywordField(),
            'title': TranslatedTextField('title'),
            'description': TranslatedTextField('description')
        }
    )
    subscriptions = fields.NestedField(
        properties={
            'user_id': fields.IntegerField(),
            'subscription_id': fields.IntegerField()
        }
    )
    downloads_count = fields.IntegerField()
    verified = fields.DateField()
    image_url = fields.TextField(attr='image_url')
    image_alt = TranslatedTextField('image_alt')

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['common']
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'max_result_window': 25000
        }

    class Django:
        model = Dataset
        related_models = [Organization, Category, Application, Article, Resource, UserFollowingDataset, DataSource]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, UserFollowingDataset):
            return related_instance.follower.followed_applications.all()
        if isinstance(related_instance, Application):
            return related_instance.datasets.filter(status='published')
        if isinstance(related_instance, Article):
            return related_instance.datasets.filter(status='published')
        if isinstance(related_instance, Resource):
            return related_instance.dataset
        if isinstance(related_instance, Category):
            return related_instance.dataset_set.filter(status='published')
        if isinstance(related_instance, Organization):
            return related_instance.datasets.filter(status='published')
        if isinstance(related_instance, DataSource):
            return related_instance.datasource_datasets.filter(status='published')

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

    def prepare_search_date(self, instance):
        return instance.verified

    def prepare_visualization_types(self, instance):
        visualization_types = instance.visualization_types
        return visualization_types if visualization_types else ['none']

    def prepare_source(self, instance):
        if not instance.source:
            return {}
        update_frq_text_val = next(freq[1] for freq in FREQUENCY_CHOICES if freq[0] == instance.source.frequency_in_days)
        return {
            'source_type': instance.source.source_type,
            'url': instance.source.url,
            'title': instance.source.title,
            'last_import_timestamp': instance.source.last_import_timestamp,
            'update_frequency': lazy_proxy_to_es_translated_field(update_frq_text_val),
        }


DatasetDocumentActive = get_active_document(unified_document=DatasetDocument, legacy_document=DatasetsDoc)
