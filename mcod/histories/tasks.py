from django.utils.timezone import now

from mcod.celeryapp import app
from mcod.histories.documents import HistoriesDoc
from mcod.histories.models import History, HistoryIndexSync


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
def save_history_as_log_entry(history_id, is_history_other):
    obj = History.objects.get_item(history_id, is_history_other)
    if obj:
        log_entry, created = obj.create_log_entry()
        if log_entry:
            return {'id': log_entry.id, 'created': created}
    return {}
