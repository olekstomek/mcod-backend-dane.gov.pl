# Generated by Django 2.1.4 on 2019-03-04 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0012_resource_tabular_data_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='data_date',
            field=models.DateField(null=True, verbose_name='Data date'),
        ),
    ]