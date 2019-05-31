from celery import shared_task

from mcod.counters.lib import Counter


@shared_task
def save_counters():
    counter = Counter()
    counter.save_counters()
    return {}
