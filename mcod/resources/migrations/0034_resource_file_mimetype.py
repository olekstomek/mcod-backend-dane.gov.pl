# Generated by Django 2.2.9 on 2021-03-17 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0033_resource_forced_api_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='file_mimetype',
            field=models.TextField(blank=True, editable=False, null=True, verbose_name='File mimetype'),
        ),
    ]