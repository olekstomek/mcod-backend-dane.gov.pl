# Generated by Django 2.0.4 on 2019-02-05 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_results', '0001_initial'),
        ('resources', '0010_resource_draft_status_and_is_removed_according_to_dataset'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskResult',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('django_celery_results.taskresult',),
        ),
        migrations.AlterField(
            model_name='resource',
            name='data_tasks',
            field=models.ManyToManyField(blank=True, related_name='data_task_resources', to='resources.TaskResult', verbose_name='Download Tasks'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='file_tasks',
            field=models.ManyToManyField(blank=True, related_name='file_task_resources', to='resources.TaskResult', verbose_name='Download Tasks'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='link_tasks',
            field=models.ManyToManyField(blank=True, related_name='link_task_resources', to='resources.TaskResult', verbose_name='Download Tasks'),
        ),
    ]
