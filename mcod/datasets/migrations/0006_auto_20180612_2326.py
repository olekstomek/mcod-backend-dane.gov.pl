# Generated by Django 2.0.4 on 2018-06-12 21:26

from django.db import migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0004_dataset_license'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified'),
        ),
    ]