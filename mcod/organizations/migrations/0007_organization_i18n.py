# Generated by Django 2.1.4 on 2019-02-25 09:57

from django.db import migrations
import modeltrans.fields


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0006_auto_20190131_1157'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='i18n',
            field=modeltrans.fields.TranslationField(fields=('slug', 'title', 'description'), required_languages=(), virtual_fields=True),
        ),
    ]
