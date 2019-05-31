from dal_admin_filters import AutocompleteFilter
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, FieldDoesNotExist
from django.db.models import Subquery, OuterRef, ManyToManyField
from django.forms.models import model_to_dict
from django.http.response import HttpResponseRedirect, Http404
from django.urls import reverse, path
from django.utils import formats
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult

from mcod.lib.admin_mixins import TrashMixin, HistoryMixin, LangFieldsOnlyMixin
from mcod.reports.admin import ExportCsvMixin
from mcod.resources.forms import ChangeResourceForm, AddResourceForm, TrashResourceForm
from mcod.resources.models import Resource, ResourceTrash

task_status_to_css_class = {
    'SUCCESS': 'fas fa-check-circle text-success',
    'PENDING': 'fas fa-question-circle text-warning',
    'FAILURE': 'fas fa-times-circle text-error',
    None: 'fas fa-minus-circle text-light'
}


class DatasetFilter(AutocompleteFilter):
    field_name = 'dataset'
    autocomplete_url = 'dataset-autocomplete'
    is_placeholder_title = False
    widget_attrs = {
        'data-placeholder': _('Filter by dataset name')
    }


class TaskStatus(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        return (
            ('SUCCESS', 'SUCCESS'),
            ('FAILURE', 'ERROR'),
            ('PENDING', 'WAITING'),
            ('N/A', 'UNAVAILABLE')
        )

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset
        val = None if val == 'N/A' else val
        return queryset.filter(**{self.qs_param: val})


class LinkStatusFilter(TaskStatus):
    title = _('Link status')
    parameter_name = 'link_status'
    qs_param = '_link_status'


class FileStatusFilter(TaskStatus):
    title = _('File status')
    parameter_name = 'file_status'
    qs_param = '_file_status'


class TabularViewFilter(TaskStatus):
    title = _('TabularView')
    parameter_name = 'tabular_view_status'
    qs_param = '_data_status'


class TaskResultInline(admin.options.InlineModelAdmin):
    template = 'admin/resources/task-inline-list.html'

    def has_change_permission(self, request, obj=None):
        return not request.POST


class FileTaskResultInline(TaskResultInline):
    model = Resource.file_tasks.through
    suit_classes = 'suit-tab suit-tab-file'


class LinkTaskResultInline(TaskResultInline):
    model = Resource.link_tasks.through
    suit_classes = 'suit-tab suit-tab-link'


class DataTaskResultInline(TaskResultInline):
    model = Resource.data_tasks.through
    suit_classes = 'suit-tab suit-tab-data'


@admin.register(Resource)
class ResourceAdmin(HistoryMixin, ExportCsvMixin, LangFieldsOnlyMixin, admin.ModelAdmin):
    actions_on_top = True
    change_suit_form_tabs = (
        ('general', _('General')),
        *LangFieldsOnlyMixin.get_traslations_tabs(),
        ('file', _('File validation')),
        ('link', _('Link validation')),
        ('data', _('Data validation'))
    )

    add_suit_form_tabs = (
        ('general', _('General')),
        *LangFieldsOnlyMixin.get_traslations_tabs()
    )

    change_fieldsets = [
        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general'),
                'fields': (
                    'link',
                    'file',
                    'packed_file',
                    'title',
                    'description',
                    'format',
                    'dataset',
                    'data_date',
                    'status',
                    'show_tabular_view',
                    'modified',
                    'created',
                    'verified',
                    'type',
                    'file_info',
                    'file_encoding',

                )
            }
        ),
    ]

    add_fieldsets = [
        (None, {
            'classes': ('suit-tab', 'suit-tab-general'),
            'fields': ('switcher', 'file', 'link'),
        }),
        (None, {
            'classes': ('suit-tab', 'suit-tab-general'),
            'fields': ('title', 'description'),
        }),
        (None, {
            'classes': ('suit-tab', 'suit-tab-general'),
            'fields': ('dataset',),
        }),
        (None, {
            'classes': ('suit-tab', 'suit-tab-general'),
            'fields': ('data_date',),
        }),
        (None, {
            'classes': ('suit-tab', 'suit-tab-general'),
            'fields': ('status',),
        }),
    ]

    change_readonly_fields = (
        'format',
        'file',
        'packed_file',
        'link',
        'modified',
        'created',
        'verified',
        'type',
        'file_info',
        'file_encoding',
        'link_tasks',
        'file_tasks',
        'data_tasks',
    )

    add_readonly_fields = ()

    list_display = [
        'title',
        'uuid',
        'format',
        'dataset',
        'status',
        'type',
        'link_status',
        'file_status',
        'tabular_view',
        'created'
        # 'obj_history'
    ]

    list_filter = [
        DatasetFilter,
        "format",
        "type",
        "status",
        LinkStatusFilter,
        FileStatusFilter,
        TabularViewFilter
    ]
    search_fields = ['title', 'uuid']
    autocomplete_fields = ['dataset']
    add_form = AddResourceForm
    form = ChangeResourceForm

    inlines = [
        FileTaskResultInline,
        DataTaskResultInline,
        LinkTaskResultInline
    ]

    def get_fieldsets(self, request, obj=None):
        return (self.change_fieldsets if obj else self.add_fieldsets) + self.get_translations_fieldsets()

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj=obj, **defaults)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = self.change_readonly_fields if obj and obj.id else self.add_readonly_fields
        if obj and obj.data_is_valid != 'SUCCESS':
            readonly_fields = (*readonly_fields, 'show_tabular_view')
        if obj and obj.type != "file":
            readonly_fields = (*readonly_fields, 'data_date')
        return readonly_fields

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context.update(
            {
                'suit_form_tabs': self.change_suit_form_tabs if obj else self.add_suit_form_tabs
            }
        )
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_staff and not request.user.is_superuser:
            qs = qs.filter(dataset__organization__in=request.user.organizations.iterator())

        link_tasks = TaskResult.objects.filter(link_task_resources=OuterRef('pk')).order_by('-date_done')
        qs = qs.annotate(
            _link_status=Subquery(
                link_tasks.values('status')[:1])
        )
        file_tasks = TaskResult.objects.filter(file_task_resources=OuterRef('pk')).order_by('-date_done')
        qs = qs.annotate(
            _file_status=Subquery(
                file_tasks.values('status')[:1])
        )

        data_tasks = TaskResult.objects.filter(data_task_resources=OuterRef('pk')).order_by('-date_done')
        qs = qs.annotate(
            _data_status=Subquery(
                data_tasks.values('status')[:1])
        )

        return qs

    def get_field_queryset(self, db, db_field, request):
        if 'object_id' in request.resolver_match.kwargs:
            resource_id = int(request.resolver_match.kwargs['object_id'])
            if db_field.name == 'link_tasks':
                return db_field.remote_field.model._default_manager.filter(
                    link_task_resources__id=resource_id,
                )
            if db_field.name == 'file_tasks':
                return db_field.remote_field.model._default_manager.filter(
                    file_task_resources__id=resource_id,
                )
            if db_field.name == 'data_tasks':
                return db_field.remote_field.model._default_manager.filter(
                    data_task_resources__id=resource_id,
                )

        super().get_field_queryset(db, db_field, request)

    def _format_list_status(self, val):
        return format_html('<i class="%s"></i>' % task_status_to_css_class[val])

    def link_status(self, obj):
        return self._format_list_status(obj._link_status)

    link_status.admin_order_field = '_link_status'
    link_status.short_description = format_html('<i class="fas fa-link"></i>')

    def file_status(self, obj):
        return self._format_list_status(obj._file_status)

    file_status.admin_order_field = '_file_status'
    file_status.short_description = format_html('<i class="fas fa-file"></i>')

    def tabular_view(self, obj):
        return self._format_list_status(obj._data_status)

    tabular_view.admin_order_field = '_data_status'
    tabular_view.short_description = format_html('<i class="fas fa-table"></i>')

    def actualized_date(self, obj):
        if obj._actualized:
            return formats.date_format(obj._actualized, format="DATETIME_FORMAT", use_l10n=True)

    actualized_date.short_description = _('Actualization date')
    actualized_date.admin_order_field = '_actualized'

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.save()

    def get_changeform_initial_data(self, request):
        """
        Get the initial form data from the request's GET params.
        """

        obj_id = request.GET.get('from_id')
        initial = {}
        if obj_id:
            data = model_to_dict(Resource.objects.get(pk=obj_id))
            initial['title'] = data.get('title')
            initial['description'] = data.get('description')
            initial['status'] = data.get('status')
            initial['dataset'] = data.get('dataset')

        for k in initial:
            try:
                f = self.model._meta.get_field(k)
            except FieldDoesNotExist:
                continue
            # We have to special-case M2Ms as a list of comma-separated PKs.
            if isinstance(f, ManyToManyField):
                initial[k] = initial[k].split(",")
        return initial

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:resource_id>/revalidate/', self.revalidate, name='resource-revalidate')
        ]
        return custom_urls + urls

    def revalidate(self, request, resource_id, *args, **kwargs):
        if not self.has_change_permission(request):
            raise PermissionDenied

        try:
            resource = self.model.objects.get(pk=resource_id)
        except self.model.DoesNotExist:
            return Http404(_('Resource with this id does not exists'))

        resource.revalidate()
        messages.add_message(request, messages.SUCCESS, _('Task for resource revalidation queued'))

        url = reverse(
            'admin:resources_resource_change',
            args=[resource_id],
            current_app=self.admin_site.name,
        )
        return HttpResponseRedirect(url)

    class Media:
        css = {
            'all': ('./fontawesome/css/all.min.css',)
        }


@admin.register(ResourceTrash)
class TrashAdmin(TrashMixin):
    list_display = ['title', 'dataset', 'modified']
    search_fields = ['title', 'dataset__title']
    fields = [
        'file',
        'link',
        'title',
        'description',
        'dataset',
        'status',
        'created',
        'modified',
        'verified',
        'data_date',
        'is_removed',
    ]

    readonly_fields = [
        'file',
        'link',
        'title',
        'description',
        'dataset',
        'status',
        'created',
        'modified',
        'verified',
        'data_date'
    ]

    form = TrashResourceForm

    def get_queryset(self, request):
        qs = Resource.deleted.all()
        if request.user.is_superuser:
            return qs
        return qs.filter(dataset__organization_id__in=request.user.organizations.all())
