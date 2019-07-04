# Generated by Django 2.0.4 on 2018-10-31 15:27

import logging

from django.db import migrations, models
from django.db.models import CharField
from django.db.models.functions import Length

CharField.register_lookup(Length, 'length')
logger = logging.getLogger('mcod')


class Migration(migrations.Migration):
    dependencies = [
        ('datasets', '0006_auto_20180612_2326'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DatasetTrash',
        ),
        migrations.CreateModel(
            name='Trash',
            fields=[
            ],
            options={
                'verbose_name': 'Trash',
                'verbose_name_plural': 'Trash',
                'proxy': True,
                'indexes': [],
            },
            bases=('datasets.dataset',),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='slug',
            field=models.SlugField(max_length=600, unique=True),
        ),

    ]