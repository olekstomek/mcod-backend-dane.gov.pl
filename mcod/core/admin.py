from auditlog.admin import (
    LogEntryAdmin as BaseLogEntryAdmin,
    ResourceTypeFilter as BaseResourceTypeFilter,
)
from auditlog.models import LogEntry
from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils import timezone
from django.utils.formats import localize
from django.utils.translation import gettext_lazy as _

from mcod.lib.admin_mixins import MCODAdminMixin


class ResourceTypeFilter(BaseResourceTypeFilter):
    title = _('table name')


class LogEntryAdmin(MCODAdminMixin, BaseLogEntryAdmin):

    list_display = ['id', '_action', '_table_name', '_row_id', '_message']
    list_filter = ['action', ResourceTypeFilter]
    fields = [
        '_table_name',
        '_row_id',
        '_action',
        '_changes',
        '_actor',
        '_timestamp',
    ]
    fieldsets = None
    readonly_fields = [x for x in fields]
    search_fields = ['object_id']

    def _action(self, obj):
        return obj.action_display
    _action.short_description = _('action')
    _action.admin_order_field = 'action'

    def _actor(self, obj):
        return obj.actor
    _actor.short_description = _('user')

    def _changes(self, obj):
        return obj.diff_prettified
    _changes.short_description = _('Differences')

    def _table_name(self, obj):
        return obj.table_name
    _table_name.short_description = _('table name')

    def _timestamp(self, obj):
        return localize(timezone.localtime(obj.timestamp))
    _timestamp.short_description = _('Change timestamp')

    def _row_id(self, obj):
        return obj.row_id
    _row_id.short_description = _('row id')
    _row_id.admin_order_field = 'object_id'

    def _message(self, obj):
        return obj.additional_data
    _message.short_description = _('message')
    _message.admin_order_field = 'additional_data'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        models = ['member', 'application_tag', 'dataset_tag', 'article_tag', 'application_dataset']  # extend later.
        return qs.exclude(content_type__model__in=models)


admin.site.unregister(Group)
admin.site.unregister(LogEntry)
