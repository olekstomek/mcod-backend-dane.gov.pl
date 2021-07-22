from dal_admin_filters import AutocompleteFilter
from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rangefilter.filter import DateRangeFilter

from mcod.lib.admin_mixins import (
    DynamicAdminListDisplayMixin,
    MCODAdminMixin,
    OrderedByDisplayAdminMixin,
    TaskStatusLabelAdminMixin,
)
from mcod.reports.models import (
    DatasetReport,
    MonitoringReport,
    OrganizationReport,
    Report,
    ResourceReport,
    SummaryDailyReport,
    UserReport,
)
from mcod.reports.tasks import generate_csv, create_daily_resources_report


class UserFilter(AutocompleteFilter):
    field_name = 'ordered_by'
    autocomplete_url = 'admin-autocomplete'
    is_placeholder_title = False
    widget_attrs = {
        'data-placeholder': _('Ordered by')
    }


class ReportsAdmin(DynamicAdminListDisplayMixin, OrderedByDisplayAdminMixin,
                   TaskStatusLabelAdminMixin, MCODAdminMixin, admin.ModelAdmin):
    model = Report
    list_display = ('file_name', 'file_size', 'ordered_by', 'created', 'status')
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

    def status_label(self, obj):
        return super().status_label(obj)

    status_label.short_description = _('status')
    status_label.admin_order_field = None


class MonitoringReportsAdmin(ReportsAdmin):
    app_models = [
        'applications.ApplicationProposal',
        'suggestions.DatasetSubmission',
        'suggestions.DatasetComment',
        'suggestions.ResourceComment',
    ]

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


def export_to_csv(self, request, queryset):
    generate_csv.s(tuple(obj.id for obj in queryset),
                   self.model._meta.label,
                   request.user.id,
                   now().strftime('%Y%m%d%H%M%S.%s')
                   ).apply_async(countdown=1)
    messages.add_message(request, messages.SUCCESS, _('Task for CSV generation queued'))


export_to_csv.short_description = _("Export selected to CSV")


class ExportCsvMixin:
    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.is_superuser:
            actions.update({
                'export_to_csv': (export_to_csv, 'export_to_csv', _("Export selected to CSV"))
            })
        return actions


admin.site.register(MonitoringReport, MonitoringReportsAdmin)
