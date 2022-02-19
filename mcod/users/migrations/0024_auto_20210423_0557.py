# Generated by Django 2.2.9 on 2021-04-23 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_user_discourse_api_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='discourse_user_name',
            field=models.CharField(blank=True, editable=False, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='discourse_api_key',
            field=models.CharField(blank=True, editable=False, max_length=100, null=True),
        ),
    ]