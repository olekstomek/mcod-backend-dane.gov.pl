# Generated by Django 2.2.9 on 2021-05-17 15:32

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('suggestions', '0029_auto_20210423_1750'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='submissionfeedback',
            managers=[
                ('raw', django.db.models.manager.Manager()),
            ],
        ),
    ]
