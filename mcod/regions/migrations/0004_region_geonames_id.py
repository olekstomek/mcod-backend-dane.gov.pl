# Generated by Django 2.2.9 on 2021-11-05 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regions', '0003_create_default_region'),
    ]

    operations = [
        migrations.AddField(
            model_name='region',
            name='geonames_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]