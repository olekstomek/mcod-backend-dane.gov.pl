# Generated by Django 2.2.9 on 2021-04-23 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0009_schedule_is_blocked'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='is_permanently_removed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='schedule',
            name='is_permanently_removed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userschedule',
            name='is_permanently_removed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userscheduleitem',
            name='is_permanently_removed',
            field=models.BooleanField(default=False),
        ),
    ]