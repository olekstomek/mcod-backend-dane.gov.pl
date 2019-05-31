from django.apps import apps
from django.conf import settings
from django_elasticsearch_dsl import DocType, Index, fields

from mcod.datasets.documents import datasets_field
from mcod.lib.search.fields import TranslatedTextField, TranslatedKeywordField

Organization = apps.get_model('organizations', 'Organization')
Dataset = apps.get_model('datasets', 'Dataset')

INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES['institutions'])
INDEX.settings(**settings.ELASTICSEARCH_DSL_INDEX_SETTINGS)


@INDEX.doc_type
class InstitutionDoc(DocType):
    id = fields.IntegerField()
    slug = TranslatedKeywordField('slug')
    title = TranslatedTextField('title', common_params={'suggest': fields.CompletionField()})
    description = TranslatedTextField('description')
    image_url = fields.TextField(
        attr='image_url'
    )

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
    status = fields.TextField()
    modified = fields.DateField()
    created = fields.DateField()

    class Meta:
        doc_type = 'institution'
        model = Organization
        related_models = [Dataset]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.organization

    def get_queryset(self):
        return self._doc_type.model.objects.filter(status='published')
