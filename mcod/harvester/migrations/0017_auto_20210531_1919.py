# Generated by Django 2.2.9 on 2021-05-31 17:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('harvester', '0016_auto_20210519_1158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasource',
            name='category',
            field=models.ForeignKey(blank=True, limit_choices_to=models.Q(code=''), null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='category_datasources', to='categories.Category', verbose_name='category'),
        ),
    ]