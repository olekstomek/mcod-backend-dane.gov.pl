# Generated by Django 2.2 on 2020-01-10 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0024_auto_20191121_1526'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='availability',
            field=models.CharField(blank=True, editable=False, max_length=6, null=True, verbose_name='availability'),
        ),
    ]