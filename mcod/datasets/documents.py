from django.apps import apps
from django_elasticsearch_dsl import DocType, Index, fields
from mcod.users.models import UserFollowingDataset

from mcod import settings
from mcod.lib.search.fields import TranslatedTextField, TranslatedKeywordField, TranslatedKeywordsList

Dataset = apps.get_model('datasets', 'Dataset')
Organization = apps.get_model('organizations', 'Organization')
Category = apps.get_model('categories', 'Category')
Tag = apps.get_model('tags', 'Tag')
Resource = apps.get_model('resources', 'Resource')
Article = apps.get_model('articles', 'Article')
Application = apps.get_model('applications', 'Application')

INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES['datasets'])
INDEX.settings(**settings.ELASTICSEARCH_DSL_INDEX_SETTINGS)


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


@INDEX.doc_type
class DatasetsDoc(DocType):
    id = fields.IntegerField()
    slug = TranslatedKeywordField('slug')
    title = TranslatedTextField('title', common_params={'suggest': fields.CompletionField()})
    version = fields.KeywordField()
    url = fields.KeywordField()
    notes = TranslatedTextField('notes')

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
    # customfields = fields.TextField()
    formats = fields.KeywordField(attr='formats', multi=True)

    license_condition_db_or_copyrighted = fields.TextField()
    license_condition_modification = fields.BooleanField()
    license_condition_original = fields.BooleanField()
    license_condition_responsibilities = fields.TextField()
    license_condition_source = fields.BooleanField()
    license_condition_timestamp = fields.BooleanField()
    license_name = fields.StringField(attr='license_name')
    license_description = fields.StringField(attr='license_description')
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

    class Meta:
        doc_type = 'dataset'
        model = Dataset
        related_models = [Organization, Category, Application, Article, Resource, UserFollowingDataset]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, UserFollowingDataset):
            return related_instance.follower.followed_applications.all()
        if isinstance(related_instance, Application):
            return related_instance.datasets.all()
        if isinstance(related_instance, Resource):
            return related_instance.dataset
        if isinstance(related_instance, Category):
            return related_instance.dataset_set.filter(status='published')
        if isinstance(related_instance, Organization):
            return related_instance.datasets.filter(status='published')

    def get_queryset(self):
        return self._doc_type.model.objects.filter(status='published')
