from django.apps import apps
from django_elasticsearch_dsl import DocType, Index, fields

from mcod import settings
from mcod.lib.search.fields import TranslatedTextField

Resource = apps.get_model('resources', 'Resource')
Dataset = apps.get_model('datasets', 'Dataset')
TaskResult = apps.get_model('django_celery_results', "TaskResult")

INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES['resources'])
INDEX.settings(**settings.ELASTICSEARCH_DSL_INDEX_SETTINGS)

data_schema = fields.NestedField(attr='schema', properties={
    'fields': fields.NestedField(properties={
        'name': fields.KeywordField(attr='name'),
        'type': fields.KeywordField(attr='type'),
        'format': fields.KeywordField(attr='format')
    }),
    'missingValue': fields.KeywordField(attr='missingValue')
})


@INDEX.doc_type
class ResourceDoc(DocType):
    id = fields.IntegerField()
    slug = fields.TextField()
    uuid = fields.TextField()
    title = TranslatedTextField('title', common_params={'suggest': fields.CompletionField()})
    description = TranslatedTextField('description')
    file_url = fields.TextField(
        attr='file_url'
    )
    download_url = fields.TextField(
        attr='download_url'
    )
    link = fields.TextField()
    format = fields.KeywordField()
    file_size = fields.LongField()
    type = fields.KeywordField()
    openness_score = fields.IntegerField()

    dataset = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'title': TranslatedTextField('title'),
        'slug': TranslatedTextField('slug')
    })

    views_count = fields.IntegerField()
    downloads_count = fields.IntegerField()

    status = fields.TextField()
    modified = fields.DateField()
    created = fields.DateField()
    verified = fields.DateField()
    data_date = fields.DateField()

    class Meta:
        doc_type = 'resource'
        model = Resource
        related_models = [Dataset, ]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.resources.all()

    def get_queryset(self):
        return self._doc_type.model.objects.filter(status='published')
