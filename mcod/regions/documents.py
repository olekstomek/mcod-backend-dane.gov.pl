from django_elasticsearch_dsl import fields

from mcod.lib.search.fields import TranslatedTextField


def regions_field(**kwargs):
    return fields.NestedField(properties={
        'region_id': fields.IntegerField(),
        'name': TranslatedTextField('name'),
        'bbox': fields.GeoShapeField('wkt_bbox'),
        'coords': fields.GeoPointField()
    }, **kwargs)
