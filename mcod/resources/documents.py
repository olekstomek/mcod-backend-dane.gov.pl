from django.apps import apps
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from mcod import settings as mcs
from mcod.harvester.serializers import DataSourceSerializer
from mcod.lib.search.fields import TranslatedTextField
from mcod.search.documents import ExtendedDocument


Resource = apps.get_model('resources', 'Resource')
Dataset = apps.get_model('datasets', 'Dataset')
TaskResult = apps.get_model('django_celery_results', "TaskResult")
SpecialSign = apps.get_model('special_signs', 'SpecialSign')


@registry.register_document
class ResourceDocument(ExtendedDocument):
    NOTES_FIELD_NAME = 'description'
    format = fields.TextField()
    formats = fields.KeywordField(attr='formats_list', multi=True)
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
    uuid = fields.TextField()
    description = TranslatedTextField('description')

    csv_file_url = fields.TextField()
    csv_file_size = fields.LongField()
    csv_download_url = fields.TextField()

    jsonld_file_url = fields.TextField()
    jsonld_file_size = fields.LongField()
    jsonld_download_url = fields.TextField()

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

    license_code = fields.IntegerField()
    update_frequency = fields.KeywordField()
    computed_downloads_count = fields.IntegerField()
    computed_views_count = fields.IntegerField()
    has_high_value_data = fields.BooleanField()

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

    def prepare_openness_scores(self, instance):
        return [instance.openness_score]

    def prepare_source(self, instance):
        serializer = DataSourceSerializer()
        if not instance.dataset.source:
            return {}
        return serializer.dump(instance.dataset.source)
