import marshmallow as ma
import marshmallow_jsonapi as ja

from mcod.lib.fields import OldRelationship
from mcod.lib.serializers import BasicSerializer, ArgsListToDict, SearchMeta, BucketItem, TranslatedStr


class Aggregations(ArgsListToDict):
    by_format = ma.fields.Nested(BucketItem(), attribute='_filter_formats.formats.buckets', many=True)
    by_type = ma.fields.Nested(BucketItem(), attribute='_filter_types.types.buckets', many=True)
    by_openness_score = ma.fields.Nested(BucketItem(), attribute='_filter_openness_score.openness_score.buckets',
                                         many=True)


class ResourcesMeta(SearchMeta):
    aggs = ma.fields.Nested(Aggregations, attribute='aggregations')


class ResourceDataset(ja.Schema):
    id = ma.fields.Int()
    title = ma.fields.Str()

    class Meta:
        type_ = 'dataset'
        strict = True
        self_url = '/datasets/{dataset_id}'
        self_url_kwargs = {"dataset_id": "<id>"}


class ResourceSchema(ja.Schema):
    id = ma.fields.Int(dump_only=True)
    uuid = ma.fields.Str()
    title = TranslatedStr()
    description = TranslatedStr()
    category = ma.fields.Str()
    format = ma.fields.Str()
    type = ma.fields.Str()
    downloads_count = ma.fields.Integer()
    openness_score = ma.fields.Integer()
    views_count = ma.fields.Integer()
    modified = ma.fields.Str()
    created = ma.fields.Str()
    verified = ma.fields.Str()
    data_date = ma.fields.Date()
    file_url = ma.fields.Str()
    download_url = ma.fields.Str()
    link = ma.fields.Str()
    file_size = ma.fields.Integer()

    class Meta:
        type_ = 'resource'
        strict = True
        self_url_many = "/resources"
        self_url = '/resources/{resource_id}'
        self_url_kwargs = {"resource_id": "<id>"}


class ResourceSerializer(ResourceSchema, BasicSerializer):
    dataset = OldRelationship(
        related_url='/datasets/{dataset_id}',
        related_url_kwargs={'dataset_id': '<dataset.id>'},
        schema=ResourceDataset,
        many=False,
        type_='datasets'
    )

    class Meta:
        type_ = 'resource'
        strict = True
        self_url_many = "/resources"
        # self_url_many_kwargs = {"dataset_id":"<dataset.data.id>"}
        self_url = '/resources/{resource_id}'
        self_url_kwargs = {"resource_id": "<id>"}


class ResourceDataSerializer(BasicSerializer):
    id = ma.fields.Int(dump_only=True)
    schema = ma.fields.Dict()
    headers = ma.fields.List(ma.fields.Str())
    data = ma.fields.Dict()

    class Meta:
        type_ = 'resource_data'
        strict = True
        self_url = '/resources/{resource_id}/data'
        self_url_kwargs = {"resource_id": "<id>"}
