from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.translation import gettext_lazy as _
from modeltrans.fields import TranslationField

from mcod.core.db.models import BaseExtendedModel
from mcod.regions.managers import RegionManager
from django_elasticsearch_dsl.registries import registry
from mcod.regions.api import PlaceholderApi

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
            reg_data, all_regions_ids = placeholder.get_all_regions_details(values)
            existing_regions = Region.objects.filter(region_id__in=all_regions_ids)
            existing_regions_ids = list(
                existing_regions.values_list('region_id', flat=True)
            )
            to_create_regions_ids = set(all_regions_ids).difference(set(existing_regions_ids))
            to_create_regions = {reg_id: reg_data[str(reg_id)] for reg_id in to_create_regions_ids}
            created_regions = Region.objects.create_new_regions(to_create_regions)
            if created_regions:
                docs = registry.get_documents((Region,))
                for doc in docs:
                    doc().update(created_regions)
            all_regions = list(existing_regions) + created_regions
            for reg in all_regions:
                if str(reg.region_id) in values:
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
    hierarchy_label = models.CharField(max_length=250, verbose_name=_("Hierarchy label"), null=True)
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
        return self.hierarchy_label_i18n

    i18n = TranslationField(fields=("name", "hierarchy_label"))

    objects = RegionManager()

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
