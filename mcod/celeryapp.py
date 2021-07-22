from __future__ import absolute_import, unicode_literals

import os

import celery
from celery.schedules import crontab

from mcod.unleash import is_enabled


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mcod.settings.local')

app = celery.Celery('mcod')
app.config_from_object('django.conf:settings', namespace='CELERY')


@celery.signals.setup_logging.connect
def config_loggers(*args, **kwags):
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)


app.autodiscover_tasks()

app.conf.timezone = 'UTC'

app.conf.beat_schedule['kibana-statistics'] = {
    'task': 'mcod.counters.tasks.kibana_statistics',
    'options': {'queue': 'periodic'},
    'schedule': crontab(minute=0, hour=4),
}

app.conf.beat_schedule['harvester-supervisor'] = {
    'task': 'mcod.harvester.tasks.harvester_supervisor',
    'options': {'queue': 'harvester'},
    'schedule': crontab(minute=0, hour=3),
}

if is_enabled('remove_orphaned_files_task.be'):
    app.conf.beat_schedule['every-month'] = {
        'task': 'mcod.resources.tasks.remove_orphaned_files_task',
        'options': {'queue': 'resources'},
        'schedule': crontab(0, 0, day_of_month='1'),  # Execute on the first day of every month at 00:00.
    }

if is_enabled('hod.be'):
    app.conf.beat_schedule['send-schedule-notifications'] = {
        'task': 'mcod.schedules.tasks.send_schedule_notifications_task',
        'options': {'queue': 'notifications'},
        'schedule': crontab(minute=0, hour=2),
    }

if is_enabled('S23_csv_metadata.be'):
    app.conf.beat_schedule['catalog_csv_file_creation'] = {
        'task': 'mcod.datasets.tasks.create_catalog_metadata_csv_file',
        'schedule': crontab(minute=0, hour=4)
    }
