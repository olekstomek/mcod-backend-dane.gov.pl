import json

from auditlog.models import LogEntry as BaseLogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer

from mcod.core.api.search.tasks import delete_document_task, update_document_task
from mcod.histories.managers import LogEntryManager


class LogEntry(BaseLogEntry):

    objects = LogEntryManager()

    class Meta:
        get_latest_by = "timestamp"
        ordering = ["-timestamp"]
        verbose_name = _("History")
        verbose_name_plural = _("Histories")
        proxy = True

    def __str__(self):
        return f"{self.id} | {self.action_display} > {self.table_name} > {self.object_id}"

    @property
    def action_display(self):
        return self.get_action_display().upper()

    @property
    def action_name(self):
        _name = self.action_display
        return "INSERT" if _name == "CREATE" else _name

    @property
    def change_timestamp(self):
        return self.timestamp

    @property
    def change_user_id(self):
        return self.user.id if self.user else None

    @property
    def difference(self):
        return self.changes

    @property
    def diff_prettified(self):
        response = json.loads(self.changes)
        response = json.dumps(response, sort_keys=True, indent=1, ensure_ascii=False).replace("&oacute;", "ó")
        response = response[:10000]
        formatter = HtmlFormatter(style="colorful", lineseparator="<br>")
        response = highlight(response, JsonLexer(), formatter)
        style = "<style>" + formatter.get_style_defs() + "</style>"
        return mark_safe(style + response)

    @property
    def message(self):
        return None

    @property
    def row_id(self):
        return self.object_id

    @property
    def table_name(self):
        return self.content_type.model

    @property
    def user(self):
        return self.actor

    def get_changed_value(self, field_name, default_value):
        changes = json.loads(self.changes)
        field_value = changes.get(field_name)
        if field_value is None:
            val = default_value
        elif isinstance(field_value, list):
            val = field_value[1]
            if field_name == "is_removed":
                val = val == "True"
        else:
            val = field_value
        return val

    @property
    def is_create(self):
        return self.action == self.Action.CREATE

    @property
    def is_update(self):
        return self.action == self.Action.UPDATE

    @property
    def is_delete(self):
        return self.action == self.Action.DELETE

    @classmethod
    def migrate_history(cls, from_obj, obj):
        s_ct = ContentType.objects.get_for_model(obj._meta.model)
        old_history = cls.objects.get_for_object(obj)
        history = cls.objects.get_for_object(from_obj)
        if old_history.exists():
            old_history.delete()
        for item in history:
            item.id = None
            item.content_type = s_ct
            item.object_id = obj.id
            item.object_pk = str(obj.id)
            timestamp = item.timestamp
            item.save()
            item.timestamp = timestamp  # https://stackoverflow.com/q/7499767/1845230
            item.save(update_fields=["timestamp"])


@receiver(post_save, sender=LogEntry)
@receiver(post_save, sender=BaseLogEntry)
def update_log_entry_handler(sender, instance, *args, **kwargs):
    update_document_task.apply_async_on_commit(
        args=(LogEntry._meta.app_label, LogEntry._meta.object_name, instance.id), queue="history"
    )


@receiver(post_delete, sender=LogEntry)
@receiver(post_delete, sender=BaseLogEntry)
def delete_log_entry_handler(sender, instance, *args, **kwargs):
    delete_document_task.s(LogEntry._meta.app_label, LogEntry._meta.object_name, instance.id).apply_async(queue="history")
