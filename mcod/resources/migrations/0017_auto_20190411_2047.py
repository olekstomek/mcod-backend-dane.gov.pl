# Generated by Django 2.2 on 2019-04-11 18:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0016_auto_20190410_1441'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Trash',
        ),
        migrations.CreateModel(
            name='ResourceTrash',
            fields=[
            ],
            options={
                'verbose_name': 'Trash',
                'verbose_name_plural': 'Trash',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('resources.resource',),
        ),
    ]
