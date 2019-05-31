import os

from dal_admin_filters import AutocompleteFilter
from django.conf import settings
from django.contrib import admin, messages
from django.http.response import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from rangefilter.filter import DateRangeFilter

from mcod.core.utils import sizeof_fmt
from mcod.reports.models import Report, UserReport, ResourceReport, DatasetReport, OrganizationReport, \
    SummaryDailyReport
from mcod.reports.tasks import generate_csv, create_daily_resources_report


class UserFilter(AutocompleteFilter):
    field_name = 'ordered_by'
    autocomplete_url = 'admin-autocomplete'
    is_placeholder_title = False
    widget_attrs = {
        'data-placeholder': _('Ordered by')
    }


class ReportsAdmin(admin.ModelAdmin):
    model = Report
    list_display = ('file_name', 'file_size', 'ordered_by', 'created', 'status')
    list_filter = (('created', DateRangeFilter), UserFilter)
    ordering = ('-created',)

    def get_list_display_links(self, request, list_display):
        return tuple()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(model=self.app_model)

    def has_add_permission(self, request, obj=None):
        return False

    def status(self, obj):
        return obj.task.status if obj.task else 'PENDING'

    def file_name(self, obj):
        if obj.file:
            file_name = obj.file.split('/')[-1]
            return mark_safe('<a href="%s">%s</a>' % (obj.file, file_name))
        else:
            return f"({_('No file generated')})"

    file_name.short_description = _('Generated report file')

    def file_size(self, obj):
        try:
            if not obj.file:
                return f"-"
            file_path = os.path.join(settings.ROOT_DIR, obj.file.strip('/'))
            return sizeof_fmt(os.path.getsize(file_path))
        except Exception:
            return f"({_('unknown')})"

    file_size.short_description = _("File size")


@admin.register(UserReport)
class UserReportsAdmin(ReportsAdmin):
    app_model = 'users.User'

    class Media:
        pass


@admin.register(ResourceReport)
class ResourceReportsAdmin(ReportsAdmin):
    app_model = 'resources.Resource'

    class Media:
        pass


@admin.register(DatasetReport)
class DatasetReportsAdmin(ReportsAdmin):
    app_model = 'datasets.Dataset'

    class Media:
        pass


@admin.register(OrganizationReport)
class OrganizationReportsAdmin(ReportsAdmin):
    app_model = 'organizations.Organization'

    class Media:
        pass


@admin.register(SummaryDailyReport)
class DailyResourceReportsAdmin(admin.ModelAdmin):
    model = Report
    list_display = ('file_name', 'file_size', 'ordered_by', 'created', 'status')
    list_filter = (('created', DateRangeFilter), UserFilter)
    ordering = ('-created',)

    def get_list_display_links(self, request, list_display):
        return tuple()

    def has_add_permission(self, request, obj=None):
        return False

    def status(self, obj):
        return obj.task.status if obj.task else 'PENDING'

    def file_name(self, obj):
        if obj.file:
            return mark_safe('<a href="/%s">%s</a>' % (obj.file, obj.file.split('/')[-1]))
        else:
            return f"({_('No file generated')})"

    file_name.short_description = _('Generated report file')

    def file_size(self, obj):
        try:
            return sizeof_fmt(os.path.getsize(os.path.join(settings.MEDIA_ROOT, obj.file))) if obj.file else f"-"
        except FileNotFoundError:
            return f"({_('unknown')})"

    file_size.short_description = _("File size")

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

        messages.info(request, _(
            'The task of generating the report has been commissioned. The report may appear with a delay ...'))
        return HttpResponseRedirect(url)


def export_to_csv(self, request, queryset):
    generate_csv.s(tuple(obj.id for obj in queryset),
                   self.model._meta.label,
                   request.user.id,
                   now().strftime('%Y%m%d%H%M%S.%s')
                   ).apply_async(countdown=1)
    messages.add_message(request, messages.SUCCESS, _('Task for CSV generation queued'))


export_to_csv.short_description = _("Export selected to CSV")


class ExportCsvMixin(object):
    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.is_superuser:
            actions.update({
                'export_to_csv': (export_to_csv, 'export_to_csv', _("Export selected to CSV"))
            })
        return actions
