# Generated by Django 2.1.4 on 2019-02-25 09:57

from django.db import migrations
import modeltrans.fields


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0010_auto_20190205_1352'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='i18n',
            field=modeltrans.fields.TranslationField(fields=('title', 'slug', 'notes'), required_languages=(), virtual_fields=True),
        ),
    ]
