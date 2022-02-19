# Generated by Django 2.2.9 on 2021-10-28 14:20

from django.db import migrations
import mcod.regions.models


class Migration(migrations.Migration):

    dependencies = [
        ('regions', '0001_initial'),
        ('resources', '0047_auto_20211012_1443'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='regions',
            field=mcod.regions.models.RegionManyToManyField(blank=True, related_name='region_resources', related_query_name='resource', through='regions.ResourceRegion', to='regions.Region', verbose_name='Regions'),
        ),
    ]