# Generated by Django 2.2.9 on 2021-06-29 12:18
import os

from django.db import migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0009_converted_formats_in_daily_report'),
    ]

    operations = [
        migrations.RunSQL(
            sql=open(
                os.path.join(settings.DATABASE_DIR, 'ODSOFT-2225-daily-report-with-new-counters.sql')
            ).read(),
            reverse_sql=open(os.path.join(settings.DATABASE_DIR,
                                          'ODSOFT-2225-daily-report-with-new-counters-backward.sql')).read(),
        )
    ]