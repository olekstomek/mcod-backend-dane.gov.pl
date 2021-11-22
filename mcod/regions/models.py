from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.translation import gettext_lazy as _
from modeltrans.fields import TranslationField

from mcod.core.db.models import BaseExtendedModel
from mcod.regions.api import PlaceholderApi, PeliasApi


# Create your models here.


class RegionManyToManyField(models.ManyToManyField):

    def save_form_data(self, instance, data):
        pks = frozenset(data)
        main_regions, additional_regions = self.save_regions_data(pks)
        getattr(instance, self.attname).set(main_regions)
        getattr(instance, self.attname).add(*additional_regions, through_defaults={'is_additional': True})

    def value_from_object(self, obj):
        return [] if obj.pk is None else list(getattr(obj, self.attname).filter(
            resourceregion__is_additional=False).values_list('region_id', flat=True))

    @staticmethod
    def save_regions_data(values):
        main_regions = []
        additional_regions = []
        if values:
            placeholder = PlaceholderApi()
            pelias = PeliasApi()
            region_labels = ['locality_id', 'localadmin_id', 'county_id', 'region_id']
            additional_regions_ids = []
            main_regions_ids = []
            reg_data = placeholder.find_by_id(values)
            for region in reg_data.values():
                main_regions_ids.append(region['id'])
                place_label = f'{region["placetype"]}_id'
                parent_regions = region['lineage'][0]
                additional_regions_ids.extend(
                    [parent_regions[r_type] for r_type in region_labels if
                     parent_regions.get(r_type) and r_type != place_label])
            additional_regions_ids = list(frozenset(additional_regions_ids))
            additional_regions_details = placeholder.find_by_id(additional_regions_ids)
            all_regions_ids = main_regions_ids + additional_regions_ids
            existing_regions = Region.objects.filter(region_id__in=all_regions_ids)
            existing_regions_ids = list(
                existing_regions.values_list('region_id', flat=True)
            )
            reg_data.update(additional_regions_details)
            to_create_regions = set(all_regions_ids).difference(set(existing_regions_ids))
            wof_ids = ['whosonfirst:{}:{}'.format(reg_data[str(reg)]['placetype'], reg) for reg in to_create_regions]
            places_details = pelias.place(wof_ids)
            geonames_ids = {feat['properties']['id']: feat['properties']['addendum']['concordances']['gn:id']
                            for feat in places_details.get('features', [])
                            if feat['properties'].get('addendum') and
                            feat['properties']['addendum']['concordances'].get('gn:id')}
            to_create_regions_obj = []
            for reg_id in to_create_regions:
                region_props = dict(
                    region_id=reg_id,
                    region_type=reg_data[str(reg_id)]['placetype'],
                    name_pl=reg_data[str(reg_id)]['names']['pol'][0] if
                    reg_data[str(reg_id)]['names'].get('pol') else reg_data[str(reg_id)]['name'],
                    name_en=reg_data[str(reg_id)]['names']['eng'][0] if
                    reg_data[str(reg_id)]['names'].get('eng') else reg_data[str(reg_id)]['name'],
                    bbox=reg_data[str(reg_id)]['geom']['bbox'].split(','),
                    lat=reg_data[str(reg_id)]['geom']['lat'],
                    lng=reg_data[str(reg_id)]['geom']['lon']
                )
                gn_id = geonames_ids.get(str(reg_id))
                if gn_id:
                    region_props['geonames_id'] = gn_id
                to_create_regions_obj.append(Region(**region_props))
            created_regions = Region.objects.bulk_create(to_create_regions_obj)
            all_regions = list(existing_regions) + created_regions
            for reg in all_regions:
                if reg.region_id in main_regions_ids:
                    main_regions.append(reg)
                else:
                    additional_regions.append(reg)
        return main_regions, additional_regions


class Region(BaseExtendedModel):
    REGION_TYPES = (('locality', _('locality')),
                    ('localadmin', _('localadmin')),
                    ('county', _('county')),
                    ('region', _('region')),
                    ('country', _('country'))
                    )
    name = models.CharField(max_length=150, verbose_name=_("title"))
    region_id = models.PositiveIntegerField()
    region_type = models.CharField(max_length=15, choices=REGION_TYPES)
    bbox = JSONField(blank=True, null=True, verbose_name=_('Boundary box'))
    lat = models.DecimalField(max_digits=10, decimal_places=8, verbose_name=_('Latitude'))
    lng = models.DecimalField(max_digits=10, decimal_places=8, verbose_name=_('Longitude'))
    geonames_id = models.PositiveIntegerField(null=True, blank=True)

    @property
    def coords(self):
        return {'lat': self.lat, 'lon': self.lng}

    @property
    def wkt_bbox(self):
        return f'BBOX ({self.bbox[0]},{self.bbox[2]},{self.bbox[1]},{self.bbox[3]})'

    @property
    def wkt_centroid(self):
        return f'POINT ({self.lat} {self.lng})'

    @property
    def geonames_url(self):
        return f'http://sws.geonames.org/{self.geonames_id}/' if self.geonames_id is not None else None

    def __str__(self):
        return f'{self.get_region_type_display()}: {self.name}'

    i18n = TranslationField(fields=("name",))

    class Meta:
        indexes = [GinIndex(fields=["i18n"])]


class ResourceRegion(models.Model):
    region = models.ForeignKey('regions.Region', models.CASCADE)
    resource = models.ForeignKey('resources.Resource', models.CASCADE)
    is_additional = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ('region', 'resource'),
        ]
