# Generated by Django 2.2.9 on 2022-02-04 14:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('showcases', '0005_auto_20211221_1904'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='showcase',
            name='file',
        ),
        migrations.RemoveField(
            model_name='showcaseproposal',
            name='file',
        ),
    ]
