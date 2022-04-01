from dal_admin_filters import AutocompleteFilter
from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from rangefilter.filter import DateRangeFilter

from mcod.lib.admin_mixins import ModelAdmin
from mcod.reports.models import (
    DatasetReport,
    MonitoringReport,
    OrganizationReport,
    Report,
    ResourceReport,
    SummaryDailyReport,
    UserReport,
)
from mcod.reports.tasks import create_daily_resources_report
from mcod.unleash import is_enabled


class UserFilter(AutocompleteFilter):
    autocomplete_url = 'admin-autocomplete'
    field_name = 'ordered_by'
    is_placeholder_title = True
    title = _('Ordered by')


class ReportsAdmin(ModelAdmin):
    model = Report
    list_display = ('file_name', 'file_size', 'ordered_by_label', 'created', 'status_label')
    list_display_links = None
    list_filter = (('created', DateRangeFilter), UserFilter)
    ordering = ('-created',)

    app_models = []

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(model__in=self.app_models) if self.app_models else queryset

    def has_add_permission(self, request, obj=None):
        return False

    def file_name(self, obj):
        if obj.file_url_path and obj.file_name:
            return mark_safe(f'<a href="{obj.file_url_path}">{obj.file_name}</a>')
        return f"({_('No file generated')})"

    file_name.short_description = _('Generated report file')

    def file_size(self, obj):
        size = obj.file_size
        return size if size is not None else format_html(f'<span class="unknown">({_("unknown")})</span>')

    file_size.short_description = _('File size')

    def get_status_value(self, obj):
        if hasattr(obj, 'task'):
            status_value = obj.task.status if obj.task else 'PENDING'
        else:
            status_value = obj.status
        return status_value

    def get_status_label(self, obj):
        if hasattr(obj, 'task'):
            status_label = _(obj.task.status) if obj.task else _('PENDING')
        else:
            status_label = _(obj.status)
        return status_label

    def status_label(self, obj):
        return super().status_label(obj)

    status_label.short_description = _('status')
    status_label.admin_order_field = None

    def ordered_by_label(self, obj):
        return self._format_user_display(obj.ordered_by.email if obj.ordered_by else '@')

    ordered_by_label.admin_order_field = 'ordered_by'
    ordered_by_label.short_description = _('Ordered by')


@admin.register(MonitoringReport)
class MonitoringReportsAdmin(ReportsAdmin):
    app_models = [
        'applications.ApplicationProposal',
        'suggestions.DatasetSubmission',
        'suggestions.DatasetComment',
        'suggestions.ResourceComment',
    ]
    if is_enabled('S39_showcases.be'):
        app_models.append('showcases.ShowcaseProposal')

    class Media:
        pass


@admin.register(UserReport)
class UserReportsAdmin(ReportsAdmin):
    app_models = ['users.User']

    class Media:
        pass


@admin.register(ResourceReport)
class ResourceReportsAdmin(ReportsAdmin):
    app_models = ['resources.Resource']

    class Media:
        pass


@admin.register(DatasetReport)
class DatasetReportsAdmin(ReportsAdmin):
    app_models = ['datasets.Dataset']

    class Media:
        pass


@admin.register(OrganizationReport)
class OrganizationReportsAdmin(ReportsAdmin):
    app_models = ['organizations.Organization']

    class Media:
        pass


@admin.register(SummaryDailyReport)
class DailyResourceReportsAdmin(ReportsAdmin):

    class Media:
        pass

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate_daily_report', self.generate_report, name='reports-generate-dailyreport')
        ]
        return urls + custom_urls

    def generate_report(self, request, *args, **kwargs):

        create_daily_resources_report.delay()

        url = reverse(
            'admin:reports_summarydailyreport_changelist',
            current_app=self.admin_site.name,
        )
        msg = _('The task of generating the report has been commissioned. The report may appear with a delay ...')
        messages.info(request, msg)
        return HttpResponseRedirect(url)
