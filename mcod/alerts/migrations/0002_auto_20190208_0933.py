# Generated by Django 2.1.4 on 2019-02-08 08:33

from django.db import migrations, models
import modeltrans.fields


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alert',
            name='finish_date',
            field=models.DateTimeField(help_text='Date and time until which the message should be displayed', verbose_name='Finish date'),
        ),
        migrations.AlterField(
            model_name='alert',
            name='i18n',
            field=modeltrans.fields.TranslationField(fields=('title', 'description'), required_languages=('pl',), virtual_fields=True),
        ),
    ]