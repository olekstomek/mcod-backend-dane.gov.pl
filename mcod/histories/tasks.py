from celery import task

from mcod.histories.documents import HistoriesDoc
from mcod.histories.models import History, HistoryIndexSync


@task
def index_history():
    last = HistoryIndexSync.objects.last()

    if last:
        doc = HistoriesDoc()
        doc.update(History.objects.filter(change_timestamp__gt=last.last_indexed).iterator())
        HistoryIndexSync.objects.create(last_indexed=History.objects.latest('change_timestamp').change_timestamp)
    return {}
