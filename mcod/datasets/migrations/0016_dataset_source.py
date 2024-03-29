# Generated by Django 2.2 on 2019-10-08 09:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('harvester', '0001_initial'),
        ('datasets', '0015_auto_20190604_2022'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='datasource_datasets', to='harvester.DataSource', verbose_name='source'),
        ),
    ]
