# Generated by Django 2.2 on 2019-06-04 18:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0011_auto_20190508_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='slug',
            field=models.SlugField(blank=True, max_length=600),
        ),
    ]