import marshmallow as ma

from mcod.datasets.depricated.serializers import DatasetSchema
from mcod.lib.fields import OldRelationship
from mcod.lib.serializers import BasicSerializer, ArgsListToDict, SearchMeta, BucketItem, TranslatedStr


class Aggregations(ArgsListToDict):
    by_city = ma.fields.Nested(BucketItem(), many=True, attribute='_filter_cities.cities.buckets')
    by_type = ma.fields.Nested(BucketItem(), many=True,
                               attribute='_filter_types.types.buckets')


class InstitutionsMeta(SearchMeta):
    aggs = ma.fields.Nested(Aggregations, attribute='aggregations')


class InstitutionsSerializer(BasicSerializer):
    id = ma.fields.Int()
    slug = TranslatedStr()
    title = TranslatedStr()
    description = TranslatedStr()
    image_url = ma.fields.Str()
    postal_code = ma.fields.Str()
    city = ma.fields.Str()
    street_type = ma.fields.Str()
    street = ma.fields.Str()
    street_number = ma.fields.Str()
    flat_number = ma.fields.Str()
    email = ma.fields.Str()
    epuap = ma.fields.Str()
    fax = ma.fields.Str(attribute='fax_display')
    tel = ma.fields.Str(attribute='phone_display')
    regon = ma.fields.Str()
    website = ma.fields.Str()
    institution_type = ma.fields.Str()
    datasets = OldRelationship(
        related_url='/institutions/{inst_id}/datasets',
        related_url_kwargs={'inst_id': '<id>'},
        schema=DatasetSchema,
        many=True,
        type_='dataset'
    )
    followed = ma.fields.Boolean()
    modified = ma.fields.Str()
    created = ma.fields.Str()

    class Meta:
        type_ = "institutions"
        self_url_many = "/institutions"
        self_url = '/institutions/{inst_id}'
        self_url_kwargs = {"inst_id": "<id>"}
