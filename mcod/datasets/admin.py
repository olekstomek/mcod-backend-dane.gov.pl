from dal_admin_filters import AutocompleteFilter
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.views.main import ChangeList
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db.models import Subquery, OuterRef
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult

from mcod.datasets.forms import DatasetForm, TrashDatasetForm
from mcod.datasets.models import Dataset, DatasetTrash
from mcod.lib.admin_mixins import TrashMixin, HistoryMixin, LangFieldsOnlyMixin
from mcod.reports.admin import ExportCsvMixin
from mcod.resources.forms import ResourceListForm, AddResourceForm
from mcod.resources.models import Resource

task_status_to_css_class = {
    'SUCCESS': 'fas fa-check-circle text-success',
    'PENDING': 'fas fa-question-circle text-warning',
    'FAILURE': 'fas fa-times-circle text-error',
    None: 'fas fa-minus-circle text-light'
}


class InlineChangeList(object):
    can_show_all = True
    multi_page = True
    get_query_string = ChangeList.__dict__['get_query_string']

    def __init__(self, request, page_num, paginator):
        self.show_all = 'all' in request.GET
        self.page_num = page_num
        self.paginator = paginator
        self.result_count = paginator.count
        self.params = dict(request.GET.items())


class PaginationInline(admin.TabularInline):
    template = 'admin/resources/tabular_paginated.html'
    per_page = 20

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super(PaginationInline, self).get_formset(
            request, obj, **kwargs)

        class PaginationFormSet(formset_class):
            def __init__(self, *args, **kwargs):
                super(PaginationFormSet, self).__init__(*args, **kwargs)

                qs = self.queryset
                paginator = Paginator(qs, self.per_page)
                try:
                    page_num = int(request.GET.get('p', '0'))
                except ValueError:
                    page_num = 0

                try:
                    page = paginator.page(page_num + 1)
                except (EmptyPage, InvalidPage):
                    page = paginator.page(paginator.num_pages)

                self.cl = InlineChangeList(request, page_num, paginator)
                self.paginator = paginator

                if self.cl.show_all:
                    self._queryset = qs
                else:
                    self._queryset = page.object_list

        PaginationFormSet.per_page = self.per_page
        return PaginationFormSet


class ChangeResourceStacked(PaginationInline):
    template = 'admin/resources/inline-list.html'
    show_change_link = True

    fields = (
        'title',
        'type',
        'format',
        'link_status',
        'file_status',
        'data_status',
        'verified',
        'data_date',
        'modified',
        'modified_by',
        'status'
    )

    sortable = 'modified'

    readonly_fields = (
        'title',
        'type',
        'format',
        'link_status',
        'file_status',
        'data_status',
        'verified',
        'data_date',
        'modified',
        'modified_by',
        'status'
    )
    max_num = 0
    min_num = 0
    extra = 3
    suit_classes = 'suit-tab suit-tab-resources'

    model = Resource
    form = ResourceListForm

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

    def data_status(self, obj):
        return self._format_list_status(obj._data_status)

    data_status.admin_order_field = '_data_status'
    data_status.short_description = format_html('<i class="fas fa-table"></i>')

    def get_queryset(self, request):
        qs = super().get_queryset(request).order_by('-modified')

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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def _get_form_for_get_fields(self, request, obj=None):
        return self.get_formset(request, obj, fields=None).form

    class Media:
        css = {
            'all': ('./fontawesome/css/all.min.css',)
        }


class AddResourceStacked(InlineModelAdmin):
    template = 'admin/resources/inline-new.html'

    show_change_link = False

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
            'fields': ('data_date', 'status',),
        }),

    ]

    add_readonly_fields = ()

    fieldsets = (
        (
            None,
            {
                'fields': ('switcher', 'file', 'link')
            }
        ),
        (
            None,
            {
                'fields': (
                    'title',
                    'description',
                    'dataset',
                    'data_date',
                    'status',
                )
            }
        ),
    )
    model = Resource
    form = AddResourceForm

    extra = 0
    suit_classes = 'suit-tab suit-tab-resources'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.none()

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial['switcher'] = 'file'
        return initial

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.modified_by = request.user
        super(AddResourceStacked, self).save_model(request, obj, form, change)

    class Media:
        css = {
            'all': ('./fontawesome/css/all.min.css',)
        }


class OrganizationFilter(AutocompleteFilter):
    field_name = 'organization'  # field name - ForeignKey to Organization model
    autocomplete_url = 'organization-autocomplete'  # url name of Organization autocomplete view
    is_placeholder_title = False  # filter title will be shown as placeholder
    widget_attrs = {
        'data-placeholder': _('Filter by institution name')
    }


@admin.register(Dataset)
class DatasetAdmin(HistoryMixin, ExportCsvMixin, LangFieldsOnlyMixin, admin.ModelAdmin):
    actions_on_top = True
    autocomplete_fields = ['tags', 'organization']
    # prepopulated_fields = {"slug": ("title",)}
    list_display = ['title', 'organization', 'created', 'created_by', 'status', 'obj_history']
    readonly_fields = [
        'slug',
        'created_by',
        'created',
        'modified',
        'verified',
    ]
    fieldsets = [
        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': (
                    "title",
                    "slug"
                )
            }
        ),
        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-tags',),
                'fields': (
                    "tags",
                )
            }
        ),
        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': (
                    "notes",
                    "url",
                    "customfields",
                    "update_frequency",
                    'organization',
                    'category',
                    'status',
                    'created_by',
                    'created',
                    'modified',
                    'verified',
                )
            }
        ),

        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-licenses',),
                'fields': (
                    "license_condition_source",
                    "license_condition_modification",
                    "license_condition_responsibilities",
                    "license_condition_db_or_copyrighted",
                )
            }
        )

    ]

    inlines = [
        ChangeResourceStacked,
        AddResourceStacked,
    ]
    search_fields = ["title", ]

    list_filter = [
        'category',
        OrganizationFilter,
        'status'
    ]
    form = DatasetForm

    suit_form_tabs = (
        ('general', _('General')),
        *LangFieldsOnlyMixin.get_traslations_tabs(),
        ('licenses', _('Conditions')),
        ('tags', _('Tags')),
        ('resources', _('Resources')),
    )

    suit_form_includes = (
        ('admin/datasets/licences/custom_include.html', 'top', 'licenses'),
    )

    def get_fieldsets(self, request, obj=None):
        return self.fieldsets + self.get_translations_fieldsets()

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        super(DatasetAdmin, self).save_model(request, obj, form, change)
        # obj.save()

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.id:
                instance.created_by = request.user
            instance.modified_by = request.user
        super(DatasetAdmin, self).save_formset(request, form, formset, change)

    def get_form(self, request, obj=None, **kwargs):
        self._request = request
        return super(DatasetAdmin, self).get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        qs = Dataset.objects.all()

        if request.user.is_superuser:
            return qs
        return qs.filter(organization_id__in=request.user.organizations.all())

    class Media:  # Empty media class is required if you are using autocomplete filter
        pass  # If you know better solution for altering admin.media from filter instance


@admin.register(DatasetTrash)
class DatasetTrashAdmin(TrashMixin):
    search_fields = ['title', 'organization__title']
    list_display = ['title', 'organization']
    fields = [
        'title',
        'slug',
        "notes",
        "url",
        "customfields",
        "update_frequency",
        'organization',
        'category',
        'status',
        'tags',
        'license_id',
        "license_condition_source",
        "license_condition_original",
        "license_condition_modification",
        "license_condition_responsibilities",
        "license_condition_db_or_copyrighted",
        'is_removed',
    ]

    readonly_fields = [
        'title',
        'slug',
        "notes",
        "url",
        "customfields",
        "update_frequency",
        'organization',
        'category',
        'status',
        'tags',
        'license_id',
        "license_condition_source",
        "license_condition_original",
        "license_condition_modification",
        "license_condition_responsibilities",
        "license_condition_db_or_copyrighted",
    ]

    form = TrashDatasetForm

    def get_queryset(self, request):
        qs = Dataset.deleted.all()
        if request.user.is_superuser:
            return qs
        return qs.filter(organization_id__in=request.user.organizations.all())
