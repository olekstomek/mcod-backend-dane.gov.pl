# Generated by Django 2.2.9 on 2022-08-12 14:56

from django.db import migrations
import django.db.models.deletion
import mcod.core.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0064_auto_20220810_0137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='related_resource',
            field=mcod.core.db.models.CustomManagerForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='related_data', to='resources.Resource', verbose_name='related data'),
        ),
    ]
