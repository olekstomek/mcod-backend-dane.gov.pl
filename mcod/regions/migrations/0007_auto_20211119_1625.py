# Generated by Django 2.2.9 on 2021-11-19 15:25
import logging
from django.db import migrations
from django.conf import settings
from django_elasticsearch_dsl.registries import registry

from mcod.regions.api import PlaceholderApi

logger = logging.getLogger('mcod')


def update_hierarchy_labels(apps, schema_editor):
    region = apps.get_model('regions', 'Region')
    placeholder = PlaceholderApi()
    all_regions = region.objects.all()
    regions_ids = list(all_regions.values_list('region_id', flat=True))
    reg_data = placeholder.find_by_id(regions_ids)
    placeholder.add_hierarchy_labels(reg_data)
    for reg in all_regions:
        try:
            reg.i18n.update(
                {'hierarchy_label_pl': reg_data[str(reg.region_id)]['hierarchy_label_pl'],
                 'hierarchy_label_en': reg_data[str(reg.region_id)]['hierarchy_label_en']}
            )
            reg.hierarchy_label = reg_data[str(reg.region_id)]['hierarchy_label_pl']
            reg.save()
        except KeyError:
            logger.debug(f'Couldn\'t update hierarchy label for region with id {reg.region_id}')
    docs = registry.get_documents((region,))
    default_reg = region.objects.get(region_id=settings.DEFAULT_REGION_ID)
    default_reg.i18n.update(
        {'hierarchy_label_pl': 'Polska',
         'hierarchy_label_en': 'Poland'}
    )
    default_reg.hierarchy_label = 'Polska'
    default_reg.save()
    for doc in docs:
        doc().update(all_regions)


class Migration(migrations.Migration):

    dependencies = [
        ('regions', '0006_auto_20211119_1600'),
    ]

    operations = [
        migrations.RunPython(update_hierarchy_labels, reverse_code=migrations.RunPython.noop),
    ]
