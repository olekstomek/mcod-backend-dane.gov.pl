# Generated by Django 2.2.9 on 2020-04-17 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0013_organization_abbreviation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='abbreviation',
            field=models.CharField(max_length=30, null=True, verbose_name='Abbreviation'),
        ),
    ]