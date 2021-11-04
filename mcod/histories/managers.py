import logging
import time
from collections import defaultdict

from django.core.paginator import Paginator
from django.db.models import Manager

logger = logging.getLogger('mcod')


class HistoryManager(Manager):

    @staticmethod
    def is_significant(status, is_removed):
        return status == 'published' and is_removed is False

    def resources_availability_as_dict(self):
        d = defaultdict(dict)
        status = None
        is_removed = None
        h = self.filter(table_name='resource').order_by('row_id', 'change_timestamp')
        p = Paginator(h, 10000)
        logger.debug('num_pages {}'.format(p.num_pages))
        last_row_id = None
        for page_nr in p.page_range:
            start = time.perf_counter()
            for i, history in enumerate(p.page(page_nr)):
                date_str = history.change_timestamp.date().strftime('%Y-%m-%d')
                key = history.row_id
                inner_key = date_str
                if last_row_id != history.row_id:
                    last_row_id = history.row_id
                    status = None
                    is_removed = None
                    assert history.action == 'INSERT'
                if history.action == 'INSERT':
                    status = history.new_value.get('status', 'draft')
                    is_removed = history.new_value.get('is_removed', True)
                    old_is_significant = self.is_significant(status, is_removed)
                    if old_is_significant:
                        d[key][inner_key] = 1
                elif history.action == 'UPDATE':
                    old_is_significant = self.is_significant(status, is_removed)
                    new_status = history.new_value.get('status', status)
                    new_is_removed = history.new_value.get('is_removed', is_removed)
                    new_is_significant = self.is_significant(new_status, new_is_removed)
                    if old_is_significant != new_is_significant:
                        if new_is_significant:
                            d[key][inner_key] = 1
                        else:
                            d[key][inner_key] = 0
                    status = new_status
                    is_removed = new_is_removed
                elif history.action == 'DELETE':
                    d[key][inner_key] = -1
            end = time.perf_counter()
            logger.debug('page_nr {}, time {}'.format(page_nr, end - start))
        return d
