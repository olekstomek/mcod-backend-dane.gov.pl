# Generated by Django 2.2.9 on 2022-01-24 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0051_resource_has_high_value_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='has_dynamic_data',
            field=models.NullBooleanField(verbose_name='dynamic data'),
        ),
    ]
