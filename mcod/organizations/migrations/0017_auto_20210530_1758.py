# Generated by Django 2.2.9 on 2021-05-30 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0016_organization_is_permanently_removed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='title',
            field=models.CharField(max_length=100, verbose_name='Name'),
        ),
    ]