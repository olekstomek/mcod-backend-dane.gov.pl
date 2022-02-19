# Generated by Django 2.2.9 on 2021-12-23 15:59

from django.db import migrations, models
import mcod.core.storages
import mcod.datasets.models


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0031_dataset_has_high_value_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='archived_resources_files',
            field=models.FileField(blank=True, max_length=2000, null=True, storage=mcod.core.storages.DatasetsArchivesStorage(base_url=None, location=None), upload_to=mcod.datasets.models.archives_upload_to, verbose_name='Archived resources files'),
        ),
    ]