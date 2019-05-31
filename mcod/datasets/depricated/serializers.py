import marshmallow as ma
import marshmallow_jsonapi as ja
from django.utils.translation import gettext as _

from mcod.datasets.models import UPDATE_FREQUENCY
from mcod.lib.fields import OldRelationship
from mcod.lib.serializers import BasicSerializer, ArgsListToDict, SearchMeta, BucketItem, TranslatedStr, \
    TranslatedTagsList
from mcod.resources.depricated.serializers import ResourceSchema

UPDATE_FREQUENCY = dict(UPDATE_FREQUENCY)


class Aggregations(ArgsListToDict):
    by_institution = ma.fields.Nested(BucketItem(app='organizations', model='Organization'),
                                      attribute='_filter_institutions.institutions.inner.buckets', many=True)
    by_category = ma.fields.Nested(BucketItem(app='categories', model='Category'),
                                   attribute='_filter_categories.categories.inner.buckets', many=True)
    by_format = ma.fields.Nested(BucketItem(), attribute='_filter_formats.formats.buckets', many=True)
    by_tag = ma.fields.Nested(BucketItem(), attribute='_filter_tags.tags.buckets', many=True)
    by_openness_scores = ma.fields.Nested(BucketItem(), attribute='_filter_openness_scores.openness_scores.buckets',
                                          many=True)


class DatasetsMeta(SearchMeta):
    aggs = ma.fields.Nested(Aggregations, attribute='aggregations')


class DatasetInstitution(ja.Schema):
    id = ma.fields.Int()
    title = TranslatedStr()
    slug = TranslatedStr()

    class Meta:
        type_ = 'institution'
        strict = True
        self_url = '/institutions/{institution_id}'
        self_url_kwargs = {"institution_id": "<id>",
                           "institution_slug": "<slug>"}


class DatasetCategory(ma.Schema):
    id = ma.fields.Int()
    title = TranslatedStr()
    description = TranslatedStr()
    image_url = ma.fields.Str()


class DatasetSchema(ja.Schema):
    id = ma.fields.Int(dump_only=True, faker_type='integer')
    slug = TranslatedStr()
    title = TranslatedStr()
    notes = TranslatedStr()
    formats = ma.fields.List(ma.fields.Str(), attr='formats')
    category = ma.fields.Nested(DatasetCategory, many=False)
    downloads_count = ma.fields.Integer()
    tags = TranslatedTagsList(TranslatedStr(), attr='tags_list')
    openness_scores = ma.fields.List(ma.fields.Int())
    license_condition_db_or_copyrighted = ma.fields.String()
    license_condition_modification = ma.fields.Boolean()
    license_condition_original = ma.fields.Boolean()
    license_condition_responsibilities = ma.fields.String()
    license_condition_source = ma.fields.Boolean()
    license_condition_timestamp = ma.fields.Boolean()
    license_name = ma.fields.String()
    license_description = ma.fields.String()
    update_frequency = ma.fields.Method('update_frequency_translated')
    views_count = ma.fields.Integer()
    url = ma.fields.String()
    modified = ma.fields.Str('last_modified_resource_date')
    created = ma.fields.Str()
    verified = ma.fields.Str()

    def last_modified_resource_date(self, obj):
        return str(obj.last_modified_resource) if obj.last_modified_resource else None

    def update_frequency_translated(self, obj):
        if obj.update_frequency and obj.update_frequency in UPDATE_FREQUENCY:
            return _(UPDATE_FREQUENCY[obj.update_frequency])
        return None

    class Meta:
        type_ = 'dataset'
        strict = True
        self_url_many = "/datasets"
        self_url = '/datasets/{dataset_id},{dataset_slug}'
        self_url_kwargs = {"dataset_id": "<id>", "dataset_slug": "<slug>"}


class DatasetSerializer(DatasetSchema, BasicSerializer):
    institution = OldRelationship(
        related_url='/institutions/{institution_id},{institution_slug}',
        related_url_kwargs={'institution_id': '<institution.id>', 'institution_slug': '<slug>'},
        schema=DatasetInstitution,
        many=False,
        type_='institution'
    )
    resources = OldRelationship(
        related_url='/datasets/{dataset_id},{dataset_slug}/resources',
        related_url_kwargs={'dataset_id': '<id>', 'dataset_slug': '<slug>'},
        schema=ResourceSchema,
        many=True,
        type_='resource'
    )

    followed = ma.fields.Boolean()

    class Meta:
        type_ = 'dataset'
        strict = True
        self_url_many = "/datasets"
        self_url = '/datasets/{dataset_id},{dataset_slug}'
        self_url_kwargs = {"dataset_id": "<id>", 'dataset_slug': '<slug>'}
