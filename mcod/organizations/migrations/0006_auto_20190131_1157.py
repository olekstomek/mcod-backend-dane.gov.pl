# Generated by Django 2.0.4 on 2019-01-31 10:57
import os
from django.db import migrations
from django.conf import settings

os.path.join(settings.DATABASE_DIR, 'MCOD-914-tel-fax-unification.sql')

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20190114_1324'),
        ('organizations', '0005_auto_20190131_1141'),
    ]

    operations = [
        migrations.RunSQL(
            open(os.path.join(settings.DATABASE_DIR, 'MCOD-914-tel-fax-unification.sql')).read()
        )
    ]