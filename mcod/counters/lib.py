import datetime

from django.apps import apps
from django.db.transaction import atomic
from django_redis import get_redis_connection
from elasticsearch.helpers import bulk as es_bulk
from elasticsearch_dsl.connections import connections

from mcod import settings

VIEWS_COUNT_PREFIX = 'views_count'
DOWNLOADS_COUNT_PREFIX = 'downloads_count'


class Counter:
    def __init__(self):
        self.con = get_redis_connection("default")

    def _get_last_save(self, oper):
        return self.con.get(f'{oper}_last_save') or "0"

    def _clear_counters(self):
        for oper in (VIEWS_COUNT_PREFIX, DOWNLOADS_COUNT_PREFIX):
            last_save = self._get_last_save(oper)
            for view in settings.COUNTED_VIEWS:
                for k in self.con.scan_iter(f'{oper}:{last_save}:{view}:*'):
                    self.con.delete(k)

    def incr_download_count(self, obj_id):
        last_save = self._get_last_save(DOWNLOADS_COUNT_PREFIX)
        key = f"{DOWNLOADS_COUNT_PREFIX}:{last_save}:resources:{obj_id}"
        self.con.incr(key)

    def incr_view_count(self, view, obj_id):
        last_save = self._get_last_save(VIEWS_COUNT_PREFIX)
        key = f"{VIEWS_COUNT_PREFIX}:{last_save}:{view}:{obj_id}"
        self.con.incr(key)

    @atomic
    def save_counters(self):
        """
        Tworzy lub uaktualnia liczniki w bazie danych i elasticsearch'u
        na podstawie wartości zapisanych w redis od ostatniej aktualizacji.

        Metoda powinna być wołana jako zadanie przez CRON.
        """

        es_actions = []
        datasets_downloads = {}

        for oper in (VIEWS_COUNT_PREFIX, DOWNLOADS_COUNT_PREFIX):
            last_save = self._get_last_save(oper)
            self.con.set(f'{oper}_last_save', str(int(datetime.datetime.now().timestamp())))

            for view in settings.COUNTED_VIEWS:
                model_name = view[:-1].title()
                model = apps.get_model(view, model_name)
                model.is_indexable = False
                for k in self.con.scan_iter(f'{oper}:{last_save}:{view}:*'):
                    obj_id = int(k.decode().split(':')[-1])
                    try:
                        obj = model.objects.get(pk=obj_id)
                    except model.DoesNotExist:
                        self.con.delete(k)
                        continue

                    incr_val = int(self.con.get(k))
                    counter = getattr(obj, oper) + incr_val
                    setattr(obj, oper, counter)
                    es_actions.append({
                        '_op_type': 'update',
                        '_index': view,
                        '_type': view[:-1],
                        '_id': obj_id,
                        'doc': {oper: counter}
                    })
                    if oper == DOWNLOADS_COUNT_PREFIX and hasattr(obj, 'dataset_id'):
                        if obj.dataset_id not in datasets_downloads:
                            datasets_downloads[obj.dataset_id] = obj.dataset.downloads_count
                        datasets_downloads[obj.dataset_id] += incr_val

                    obj.save()
                    self.con.delete(k)

        for dataset_id, counter in datasets_downloads.items():
            es_actions.append({
                '_op_type': 'update',
                '_index': 'datasets',
                '_type': 'dataset',
                '_id': dataset_id,
                'doc': {DOWNLOADS_COUNT_PREFIX: counter}
            })

        es_bulk(connections.get_connection(), actions=es_actions)
