from __future__ import absolute_import, unicode_literals

import os

import celery
import pytz
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mcod.settings.local")

app = celery.Celery("mcod")
app.config_from_object("django.conf:settings", namespace="CELERY")


@celery.signals.setup_logging.connect
def config_loggers(*args, **kwags):
    from logging.config import dictConfig

    from django.conf import settings

    dictConfig(settings.LOGGING)


app.autodiscover_tasks()

app.conf.timezone = pytz.timezone("UTC")

app.conf.beat_schedule["kibana-statistics"] = {
    "task": "mcod.counters.tasks.kibana_statistics",
    "options": {"queue": "periodic"},
    "schedule": crontab(minute=0, hour=4),
}

app.conf.beat_schedule["harvester-supervisor"] = {
    "task": "mcod.harvester.tasks.harvester_supervisor",
    "options": {"queue": "harvester"},
    "schedule": crontab(minute=0, hour=3),
}

app.conf.beat_schedule["catalog_xml_file_creation"] = {
    "task": "mcod.datasets.tasks.create_xml_metadata_files",
    "options": {"queue": "periodic"},
    "schedule": crontab(minute=0, hour=5),
}

app.conf.beat_schedule["catalog_csv_file_creation"] = {
    "task": "mcod.datasets.tasks.create_csv_metadata_files",
    "options": {"queue": "periodic"},
    "schedule": crontab(minute=30, hour=4),
}


app.conf.beat_schedule["dataset_update_reminders"] = {
    "task": "mcod.datasets.tasks.send_dataset_update_reminder",
    "options": {"queue": "periodic"},
    "schedule": crontab(minute=0, hour=6),
}

app.conf.beat_schedule["kronika_sparql_performance"] = {
    "task": "mcod.reports.tasks.check_kronika_connection_performance",
    "options": {"queue": "periodic"},
    "schedule": crontab(minute=30, hour=11),
}

app.conf.beat_schedule["dga_temp_dir_clean"] = {
    "task": "mcod.resources.tasks.clean_dga_temp_directory",
    "options": {"queue": "periodic"},
    "schedule": crontab(minute=30, hour=3),
}

app.conf.beat_schedule["dga_main_resource_creation"] = {
    "task": "mcod.resources.tasks.create_main_dga_resource_task",
    "options": {"queue": "periodic"},
    "schedule": crontab(minute=30, hour=3),
}

app.conf.beat_schedule["compare_postgres_and_elasticsearch_consistency"] = {
    "task": "mcod.resources.tasks.compare_postgres_and_elasticsearch_consistency_task",
    "kwargs": {"models_to_check": ("resources.Resource", "datasets.Dataset")},
    "options": {"queue": "periodic"},
    "schedule": crontab(minute=15, hour=6),
}
