from __future__ import absolute_import, unicode_literals

import os

import celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mcod.settings.local')

app = celery.Celery('mcod')
app.config_from_object('django.conf:settings', namespace='CELERY')


@celery.signals.setup_logging.connect
def config_loggers(*args, **kwags):
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)


app.autodiscover_tasks()

app.conf.beat_schedule = {
    'every-2-minute': {
        'task': 'mcod.counters.tasks.save_counters',
        'schedule': 120,
    },
    'every-3-minutes': {
        'task': 'mcod.histories.tasks.index_history',
        'schedule': 180,
    },
    'every-5-minutes': {
        'task': 'mcod.searchhistories.tasks.save_searchhistories_task',
        'schedule': 300,
    },
    'every-day-morning': {
        'task': 'mcod.reports.tasks.create_daily_resources_report',
        'schedule': crontab(minute=0, hour=2)

    },

}

app.conf.timezone = 'UTC'
