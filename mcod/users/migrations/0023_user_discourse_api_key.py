# Generated by Django 2.2.9 on 2021-04-23 02:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_user_from_agent'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='discourse_api_key',
            field=models.CharField(blank=True, editable=False, max_length=50, null=True),
        ),
    ]
