from django.conf import settings as mcs
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from mcod.core.db.elastic import Document
from mcod.lib.search.fields import TranslatedTextField, TranslatedSuggestField
from mcod.regions.models import Region


def regions_field(**kwargs):
    return fields.NestedField(properties={
        'region_id': fields.IntegerField(),
        'name': TranslatedTextField('name'),
        'hierarchy_label': TranslatedTextField('hierarchy_label'),
        'bbox': fields.GeoShapeField('wkt_bbox'),
        'coords': fields.GeoPointField()
    }, **kwargs)


@registry.register_document
class RegionDocument(Document):
    region_id = fields.IntegerField()
    title = TranslatedSuggestField('name')
    hierarchy_label = TranslatedTextField('hierarchy_label')
    model = fields.KeywordField()
    created = fields.DateField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['regions']
        settings = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_SETTINGS
        aliases = mcs.ELASTICSEARCH_DSL_SEARCH_INDEX_ALIAS

    class Django:
        model = Region

    def prepare_model(self, instance):
        return instance._meta.model_name
