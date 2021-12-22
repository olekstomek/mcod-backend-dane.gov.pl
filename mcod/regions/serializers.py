from django.conf import settings
from marshmallow import pre_dump

from mcod.core.api import fields
from mcod.core.api.schemas import ExtSchema
from mcod.lib.serializers import TranslatedStr
from mcod.regions.models import Region


class DefaultRegionMixin:

    @pre_dump(pass_many=True)
    def get_default_region(self, data, many, **kwargs):
        if many and not data:
            data = Region.objects.filter(region_id=settings.DEFAULT_REGION_ID)
        return data


class RegionSchema(DefaultRegionMixin, ExtSchema):
    name = TranslatedStr()
    region_id = fields.Str()
    hierarchy_label = TranslatedStr()


class RDFRegionSchema(DefaultRegionMixin, ExtSchema):
    geonames_url = fields.URL()
    centroid = fields.Str(attribute='wkt_centroid')
