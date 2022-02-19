# Generated by Django 2.2.9 on 2021-01-14 10:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0026_dataset_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='categories',
            field=models.ManyToManyField(db_table='dataset_category', limit_choices_to=models.Q(_negated=True, code=''), related_name='datasets', related_query_name='dataset', to='categories.Category', verbose_name='Categories'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='category',
            field=models.ForeignKey(blank=True, limit_choices_to=models.Q(code=''), null=True, on_delete=django.db.models.deletion.SET_NULL, to='categories.Category', verbose_name='Category'),
        ),
    ]