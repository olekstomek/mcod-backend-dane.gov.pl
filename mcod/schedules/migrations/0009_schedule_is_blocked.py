# Generated by Django 2.2.9 on 2021-02-15 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0008_add_trigram_extension'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='is_blocked',
            field=models.BooleanField(default=False, verbose_name='is blocked?'),
        ),
    ]