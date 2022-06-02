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

app.conf.beat_schedule['catalog_csv_file_creation'] = {
    'task': 'mcod.datasets.tasks.create_catalog_metadata_files',
    'options': {'queue': 'periodic'},
    'schedule': crontab(minute=30, hour=4)
}


app.conf.beat_schedule['dataset_update_reminders'] = {
    'task': 'mcod.datasets.tasks.send_dataset_update_reminder',
    'options': {'queue': 'periodic'},
    'schedule': crontab(minute=0, hour=6)
}
if not is_enabled('S51_drop_old_history_triggers.be'):
    app.conf.beat_schedule['every-3-minutes'] = {
        'task': 'mcod.histories.tasks.index_history',
        'options': {'queue': 'periodic'},
        'schedule': 180,
    }
