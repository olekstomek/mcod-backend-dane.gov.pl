from __future__ import absolute_import, unicode_literals

import os

import celery
import pytz
from celery.schedules import crontab
from django.conf import settings

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


def get_beat_schedule(enable_monthly_reports: bool) -> dict:
    """Create a schedule for Celery Beat, with monthly repors
    if `enable_monthly_reports` is `True`.
    """

    default_options = {"queue": "periodic"}
    beat_schedule = {
        "save_counters": {
            "task": "mcod.counters.tasks.save_counters",
            "options": default_options,
            "schedule": 120,
        },
        "save_searchhistories_task": {
            "task": "mcod.searchhistories.tasks.save_searchhistories_task",
            "options": default_options,
            "schedule": 300,
        },
        "update-query-watchers": {
            "task": "mcod.watchers.tasks.update_query_watchers_task",
            "options": default_options,
            "schedule": crontab(minute=0, hour=22),
        },
        "send-subscriptions-report": {
            "task": "mcod.watchers.tasks.send_report_from_subscriptions",
            "options": default_options,
            "schedule": crontab(minute=0, hour=5),
        },
        "send-schedule-notifications": {
            "task": "mcod.schedules.tasks.send_schedule_notifications_task",
            "options": default_options,
            "schedule": crontab(minute=0, hour=2),
        },
        "send-newsletter": {
            "task": "mcod.newsletter.tasks.send_newsletter",
            "options": default_options,
            "schedule": crontab(minute=0, hour=8),
        },
        "deactivate-accepted-dataset-submissions": {
            "task": "mcod.suggestions.tasks.deactivate_accepted_dataset_submissions",
            "options": default_options,
            "schedule": crontab(minute=0, hour=5),
        },
        "kibana-statistics": {
            "task": "mcod.counters.tasks.kibana_statistics",
            "options": default_options,
            "schedule": crontab(minute=0, hour=4),
        },
        "harvester-supervisor": {
            "task": "mcod.harvester.tasks.harvester_supervisor",
            "options": default_options,
            "schedule": crontab(minute=0, hour=3),
        },
        "catalog_xml_file_creation": {
            "task": "mcod.datasets.tasks.create_xml_metadata_files",
            "options": default_options,
            "schedule": crontab(minute=0, hour=5),
        },
        "catalog_csv_file_creation": {
            "task": "mcod.datasets.tasks.create_csv_metadata_files",
            "options": default_options,
            "schedule": crontab(minute=30, hour=4),
        },
        "dataset_update_reminders": {
            "task": "mcod.datasets.tasks.send_dataset_update_reminder",
            "options": default_options,
            "schedule": crontab(minute=0, hour=6),
        },
        "kronika_sparql_performance": {
            "task": "mcod.reports.tasks.check_kronika_connection_performance",
            "options": default_options,
            "schedule": crontab(minute=30, hour=11),
        },
        "dga_temp_dir_clean": {
            "task": "mcod.resources.tasks.clean_dga_temp_directory",
            "options": default_options,
            "schedule": crontab(minute=30, hour=3),
        },
        "dga_main_resource_creation": {
            "task": "mcod.resources.tasks.create_main_dga_resource_task",
            "options": default_options,
            "schedule": crontab(minute=30, hour=3),
        },
        "compare_postgres_and_elasticsearch_consistency": {
            "task": "mcod.resources.tasks.compare_postgres_and_elasticsearch_consistency_task",
            "kwargs": {"models_to_check": ("resources.Resource", "datasets.Dataset")},
            "options": default_options,
            "schedule": crontab(minute=15, hour=6),
        },
        "create_daily_resources_report": {
            "task": "mcod.reports.tasks.create_daily_resources_report",
            "options": default_options,
            "schedule": crontab(minute=0, hour=2),
        },
    }

    if enable_monthly_reports:
        beat_schedule.update(
            {
                "monthly_broken_links_report": {
                    "task": "mcod.reports.tasks.validate_resources_links",
                    "options": {"queue": "periodic"},
                    "schedule": crontab(minute=30, hour=3, day_of_month=1),
                },
                "monthly_nodata_datasets_report": {
                    "task": "mcod.reports.tasks.create_no_resource_dataset_report",
                    "options": {"queue": "periodic"},
                    "schedule": crontab(minute=0, hour=3, day_of_month=1),
                },
            }
        )

    return beat_schedule


app.conf.beat_schedule = get_beat_schedule(enable_monthly_reports=settings.ENABLE_MONTHLY_REPORTS)
