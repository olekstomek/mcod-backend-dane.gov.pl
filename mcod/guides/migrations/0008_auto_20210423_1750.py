# Generated by Django 2.2.9 on 2021-04-23 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guides', '0007_guideitem_is_expandable'),
    ]

    operations = [
        migrations.AddField(
            model_name='guide',
            name='is_permanently_removed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='guideitem',
            name='is_permanently_removed',
            field=models.BooleanField(default=False),
        ),
    ]