from django.utils.timezone import now

from mcod.celeryapp import app
from mcod.histories.documents import HistoriesDoc, LogEntryDoc
from mcod.histories.models import History, HistoryIndexSync, LogEntry, LogEntryIndexSync


@app.task
def index_history():
    last = HistoryIndexSync.objects.last()

    if last:
        doc = HistoriesDoc()
        doc.update(
            History.objects.filter(change_timestamp__gt=last.last_indexed).exclude(table_name="user").iterator()
        )
        HistoryIndexSync.objects.create(last_indexed=History.objects.latest('change_timestamp').change_timestamp)
    else:
        HistoryIndexSync.objects.create(last_indexed=now())
    return {}


@app.task
def index_logentries():
    last = LogEntryIndexSync.objects.last()
    if last:
        doc = LogEntryDoc()
        objs = LogEntry.objects.filter(timestamp__gt=last.last_indexed)\
                               .exclude(content_type__model='user').iterator()
        indexed, errors = doc.update(objs)
        last_indexed = LogEntry.objects.latest('timestamp').timestamp
    else:
        indexed = 0
        last_indexed = now()
    LogEntryIndexSync.objects.create(last_indexed=last_indexed)
    LogEntryIndexSync.objects.filter(last_indexed__lt=last_indexed).delete()  # keep max 1 obj in DB.
    return {'indexed': indexed, 'last_indexed': last_indexed}
