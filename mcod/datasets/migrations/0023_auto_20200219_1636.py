# Generated by Django 2.2.9 on 2020-02-19 15:36

from django.db import migrations


def update_downloads_count(apps, schema_editor):
    Dataset = apps.get_model('datasets', 'Dataset')
    objs = Dataset.objects.all()
    for obj in objs:
        obj.downloads_count = sum(res.downloads_count for res in obj.resources.all())
    Dataset.objects.bulk_update(objs, ['downloads_count'])


def reset_downloads_count(apps, schema_editor):
    Dataset = apps.get_model('datasets', 'Dataset')
    objs = Dataset.objects.all()
    for obj in objs:
        obj.downloads_count = 0
    Dataset.objects.bulk_update(objs, ['downloads_count'])


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0022_dataset_downloads_count'),
    ]

    operations = [
        migrations.RunPython(update_downloads_count, reverse_code=reset_downloads_count),
    ]