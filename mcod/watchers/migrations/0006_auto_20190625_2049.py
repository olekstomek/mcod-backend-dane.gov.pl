# Generated by Django 2.2 on 2019-06-25 18:49

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('watchers', '0005_watchers_triggers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='watcher',
            name='object_ident',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together={('user', 'watcher', 'name')},
        ),
    ]