# Generated by Django 2.2 on 2019-05-07 11:52

from django.db import migrations
import modeltrans.fields


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0009_auto_20190410_1441'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='i18n',
            field=modeltrans.fields.TranslationField(fields=('title', 'description', 'city', 'slug'), required_languages=(), virtual_fields=True),
        ),
    ]
