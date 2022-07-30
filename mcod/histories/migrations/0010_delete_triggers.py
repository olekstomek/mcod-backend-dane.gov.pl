# Generated by Django 2.2.9 on 2022-07-14 14:23
import os

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('histories', '0009_delete_historyindexsync'),
    ]

    operations = [
        migrations.RunSQL(
            open(os.path.join(settings.DATABASE_DIR, 'ODSOFT-3007-delete-triggers.sql')).read(),
            reverse_sql=open(os.path.join(settings.DATABASE_DIR, 'ODSOFT-3007-delete-triggers-backward.sql')).read(),
        )
    ]