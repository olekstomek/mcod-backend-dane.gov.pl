# Generated by Django 2.2.9 on 2022-06-03 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0040_auto_20220428_1122'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='is_promoted',
            field=models.BooleanField(default=False, verbose_name='promoting the dataset'),
        ),
    ]
