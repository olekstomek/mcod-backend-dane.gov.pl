# Generated by Django 2.2.9 on 2021-04-23 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('special_signs', '0004_delete_specialsigntrash'),
    ]

    operations = [
        migrations.AddField(
            model_name='specialsign',
            name='is_permanently_removed',
            field=models.BooleanField(default=False),
        ),
    ]