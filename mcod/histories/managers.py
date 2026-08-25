import logging
import time
from collections import defaultdict

from auditlog.models import LogEntryManager as BaseLogEntryManager
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator

logger = logging.getLogger("mcod")


class LogEntryManager(BaseLogEntryManager):

    def for_admin_panel(self, exclude_models=None):
        models = [
            "application",
            "article",
            "article_category",
            "category",
            "dataset",
            "organization",
            "reports_report",
            "resource",
            "showcase",
            "supplement",
            "tag",
            "user",
            "user_following_application",
            "user_following_article",
            "user_following_dataset",
            "user_organization",
        ]
        exclude_models = exclude_models if isinstance(exclude_models, list) else []
        models = [x for x in models if x not in exclude_models]
        return self.get_queryset().filter(content_type__model__in=models).select_related("content_type")

    @staticmethod
    def is_significant(status, is_removed):
        return status == "published" and is_removed is False

    def get_availability_status(self, d, log_entry, object_id, dt, status, is_removed):
        if log_entry.is_create:
            status = log_entry.get_changed_value("status", "draft")
            is_removed = log_entry.get_changed_value("is_removed", True)
            old_is_significant = self.is_significant(status, is_removed)
            if old_is_significant:
                d[object_id][dt] = 1
        elif log_entry.is_update:
            old_is_significant = self.is_significant(status, is_removed)
            new_status = log_entry.get_changed_value("status", status)
            new_is_removed = log_entry.get_changed_value("is_removed", is_removed)
            new_is_significant = self.is_significant(new_status, new_is_removed)
            if old_is_significant != new_is_significant:
                if new_is_significant:
                    d[object_id][dt] = 1
                else:
                    d[object_id][dt] = 0
            status = new_status
            is_removed = new_is_removed
        elif log_entry.is_delete:
            d[object_id][dt] = -1
        return status, is_removed

    def resources_availability_as_dict(self):
        d = defaultdict(dict)
        status = None
        is_removed = None
        resource_type = ContentType.objects.get(app_label="resources", model="resource")
        entries = self.filter(content_type_id=resource_type.pk).order_by("object_id", "timestamp")
        p = Paginator(entries, 10000)
        logger.debug("num_pages {}".format(p.num_pages))
        last_row_id = None
        for page_nr in p.page_range:
            start = time.perf_counter()
            for i, log_entry in enumerate(p.page(page_nr)):
                date_str = log_entry.timestamp.date().strftime("%Y-%m-%d")
                current_id = log_entry.object_id
                inner_key = date_str
                if last_row_id != log_entry.object_id:
                    last_row_id = log_entry.object_id
                    status = None
                    is_removed = None
                    try:
                        assert log_entry.is_create
                    except AssertionError:
                        logger.debug(
                            f"{log_entry.get_action_display()} earlier than" f" CREATE for resource {log_entry.object_id}"
                        )
                        logger.debug(f"Timestamp: {log_entry.timestamp}")
                        logger.debug(f"Changes: {log_entry.changes}")
                        continue
                status, is_removed = self.get_availability_status(d, log_entry, current_id, inner_key, status, is_removed)
            end = time.perf_counter()
            logger.debug("page_nr {}, time {}".format(page_nr, end - start))
        return d
