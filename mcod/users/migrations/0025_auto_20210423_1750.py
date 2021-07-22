# Generated by Django 2.2.9 on 2021-04-23 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0024_auto_20210423_0557'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='is_permanently_removed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='meetingfile',
            name='is_permanently_removed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_permanently_removed',
            field=models.BooleanField(default=False),
        ),
    ]
