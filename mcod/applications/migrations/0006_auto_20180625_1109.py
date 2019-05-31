# Generated by Django 2.0.4 on 2018-06-25 09:09

from django.db import migrations, models
import mcod.core.storages


class Migration(migrations.Migration):
    dependencies = [
        ('applications', '0005_auto_20180612_2326'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='image',
            field=models.ImageField(blank=True, max_length=200, null=True,
                                    storage=mcod.core.storages.ApplicationImagesStorage(base_url=None, location=None),
                                    upload_to='%Y%m%d', verbose_name='Image URL'),
        ),
    ]
