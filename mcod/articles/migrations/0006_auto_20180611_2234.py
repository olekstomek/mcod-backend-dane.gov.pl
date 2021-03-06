# Generated by Django 2.0.4 on 2018-06-11 20:34

from django.db import migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0004_auto_20180525_1430'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified'),
        ),
    ]
