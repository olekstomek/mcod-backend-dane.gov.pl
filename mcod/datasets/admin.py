from dal_admin_filters import AutocompleteFilter
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db.models import Subquery, OuterRef
from django.http import JsonResponse
from django.template.defaultfilters import yesno
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult

from mcod.datasets.forms import DatasetForm, TrashDatasetForm
from mcod.datasets.models import Dataset, DatasetTrash, UPDATE_NOTIFICATION_FREQUENCY_DEFAULT_VALUES
from mcod.lib.admin_mixins import (
    HistoryMixin,
    ModelAdmin,
    TabularInline,
    TrashMixin,
    InlineModelAdmin
)
from mcod.lib.utils import is_django_ver_lt
from mcod.resources.forms import ResourceListForm, AddResourceForm, ResourceInlineFormset
from mcod.resources.models import Resource
from mcod.unleash import is_enabled
from mcod.users.forms import FilteredSelectMultipleCustom


class InlineChangeList:
    can_show_all = True
    multi_page = True
    get_query_string = ChangeList.__dict__['get_query_string']

    def __init__(self, request, page_num, paginator, page_param='p'):
        self.show_all = 'all' in request.GET
        self.page_num = page_num
        self.paginator = paginator
        self.result_count = paginator.count
        self.params = dict(request.GET.items())
        self.page_param = page_param


class PaginationInline(TabularInline):
    template = 'admin/resources/tabular_paginated.html'
    per_page = 20
    page_param = 'p'
    verbose_name_plural = _('Resources list')

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super().get_formset(request, obj, **kwargs)

        class PaginationFormSet(formset_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                default_first_page = '0' if is_django_ver_lt(3, 2) else '1'
                queryset = self.queryset
                paginator = Paginator(queryset, self.per_page)
                try:
                    page_num = int(request.GET.get(self.page_param, default_first_page))
                except ValueError:
                    page_num = int(default_first_page)

                try:
                    _paginator_page = page_num + 1 if is_django_ver_lt(3, 2) else page_num
                    page = paginator.page(_paginator_page)
                except (EmptyPage, InvalidPage):
                    page = paginator.page(paginator.num_pages)

                self.cl = InlineChangeList(request, page_num, paginator, page_param=self.page_param)
                self.paginator = paginator

                self._queryset = queryset if self.cl.show_all else page.object_list

        PaginationFormSet.per_page = self.per_page
        PaginationFormSet.page_param = self.page_param
        return PaginationFormSet


class ChangeResourceStacked(PaginationInline):
    template = 'admin/resources/inline-list.html'
    fields = (
        '_title',
        'type',
        'formats',
        'link_status',
        'file_status',
        'data_status',
        'verified',
        'data_date',
        'modified',
        'modified_by_label',
        'status_label'
    )
    readonly_fields = fields
    sortable = 'modified'
    max_num = 0
    min_num = 0
    extra = 3
    suit_classes = 'suit-tab suit-tab-resources'
    model = Resource
    form = ResourceListForm

    def formats(self, obj):
        return obj.formats or '-'

    formats.admin_order_field = 'format'
    formats.short_description = 'Format'

    def link_status(self, obj):
        return self._format_list_status(obj._link_status)

    link_status.admin_order_field = '_link_status'

    def modified_by_label(self, obj):
        return self._format_user_display(obj.modified_by.email if obj.modified_by else '')

    modified_by_label.admin_order_field = 'modified_by'
    modified_by_label.short_description = _('Modified by')

    def file_status(self, obj):
        return self._format_list_status(obj._file_status)

    file_status.admin_order_field = '_file_status'

    def data_status(self, obj):
        return self._format_list_status(obj._data_status)

    data_status.admin_order_field = '_data_status'

    data_status.short_description = format_html('<i class="fas fa-table" title="{}"></i>'.format(
        _('Tabular data validation status')))
    file_status.short_description = format_html('<i class="fas fa-file" title="{}"></i>'.format(
        _('File validation status')))
    link_status.short_description = format_html('<i class="fas fa-link" title="{}"></i>'.format(
        _('Link validation status')))

    def get_queryset(self, request):
        queryset = super().get_queryset(request).order_by('-modified')
        if request.user.is_staff and not request.user.is_superuser:
            queryset = queryset.filter(dataset__organization__in=request.user.organizations.iterator())
        link_tasks = TaskResult.objects.filter(link_task_resources=OuterRef('pk')).order_by('-date_done')
        queryset = queryset.annotate(
            _link_status=Subquery(
                link_tasks.values('status')[:1])
        )
        file_tasks = TaskResult.objects.filter(file_task_resources=OuterRef('pk')).order_by('-date_done')
        queryset = queryset.annotate(
            _file_status=Subquery(
                file_tasks.values('status')[:1])
        )
        data_tasks = TaskResult.objects.filter(data_task_resources=OuterRef('pk')).order_by('-date_done')
        return queryset.annotate(
            _data_status=Subquery(
                data_tasks.values('status')[:1])
        )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_imported:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_imported:
            return False
        return True

    def _get_form_for_get_fields(self, request, obj=None):
        return self.get_formset(request, obj, fields=None).form

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return tuple(self.replace_attributes(fields))

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def _title(self, obj):
        return obj.title_as_link
    _title.short_description = _("title")


class AddResourceStacked(InlineModelAdmin):
    template = 'admin/resources/inline-new.html'

    show_change_link = False
    use_translated_fields = True

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

    has_dynamic_data = ['has_dynamic_data'] if is_enabled('S43_dynamic_data.be') else []
    has_high_value_data = ['has_high_value_data'] if is_enabled('S41_resource_has_high_value_data.be') else []
    has_research_data = ['has_research_data'] if is_enabled('S47_research_data.be') else []
    regions = ['regions_'] if\
        is_enabled('S45_forms_unification.be') and is_enabled('S37_resources_admin_region_data.be') else []
    _fields = (
        'title',
        'description',
        'dataset',
        *regions,
        'data_date',
        'status',
        'special_signs',
        *has_dynamic_data,
        *has_high_value_data,
        *has_research_data,
    )

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
                'fields': _fields
            }
        ),
    )
    model = Resource
    form = AddResourceForm
    if is_enabled('S40_new_file_model.be'):
        formset = ResourceInlineFormset

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
        super().save_model(request, obj, form, change)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if is_enabled('S45_forms_unification.be'):
            extended_fields = self.extend_by_lang_fields(fieldsets[1][1]['fields'])
            fieldsets[1][1]['fields'] = extended_fields
        return fieldsets


class OrganizationFilter(AutocompleteFilter):
    autocomplete_url = 'organization-autocomplete'
    field_name = 'organization'
    is_placeholder_title = True
    title = _('Filter by institution name')


@admin.register(Dataset)
class DatasetAdmin(HistoryMixin, ModelAdmin):
    actions_on_top = True
    autocomplete_fields = ['tags', 'organization']
    check_imported_obj_perms = True
    export_to_csv = True
    form = DatasetForm
    inlines = [
        ChangeResourceStacked,
        AddResourceStacked,
    ]
    list_display = [
        'title',
        'organization',
        'created',
        'created_by_label',
        'status_label',
        'obj_history',
    ]
    lang_fields = True
    list_filter = [
        'categories',
        OrganizationFilter,
        'status'
    ]
    prepopulated_fields = {
        "slug": ("title", ),
    }
    readonly_fields = [
        'created_by',
        'created',
        'modified',
        'verified',
        'dataset_logo'
    ]
    search_fields = ["title", ]
    soft_delete = True
    suit_form_includes = (
        ('admin/datasets/licences/custom_include.html', 'top', 'licenses'),
    )

    @property
    def suit_form_tabs(self):
        return (
            ('general', _('General')),
            *self.get_translations_tabs(),
            ('licenses', _('Conditions')),
            ('tags', _('Tags')),
            ('resources', _('Resources')),
        )

    def has_dynamic_data_info(self, obj):
        return yesno(obj.has_dynamic_data, 'Tak,Nie,-')
    has_dynamic_data_info.short_description = _('dynamic data')

    def has_high_value_data_info(self, obj):
        return yesno(obj.has_high_value_data, 'Tak,Nie,-')
    has_high_value_data_info.short_description = _('has high value data')

    def has_research_data_info(self, obj):
        return yesno(obj.has_research_data, 'Tak,Nie,-')
    has_research_data_info.short_description = _('has research data')

    def update_frequency_display(self, obj):
        return obj.frequency_display
    update_frequency_display.short_description = _('Update frequency')

    def get_fieldsets(self, request, obj=None):
        tags_tab_fields = ('tags_list_pl', 'tags_list_en') if obj and obj.is_imported else ('tags_pl', 'tags_en')
        update_frequency_field = 'update_frequency_display' if obj and obj.is_imported else 'update_frequency'
        category_field = 'categories_list' if obj and obj.is_imported else 'categories'
        frequency_fields = []
        if not (obj and obj.is_imported):
            frequency_fields = [
                'is_update_notification_enabled',
                'update_notification_frequency',
                'update_notification_recipient_email',
            ]
        has_dynamic_data = []
        if is_enabled('S43_dynamic_data.be'):
            has_dynamic_data = ['has_dynamic_data_info'] if obj and obj.is_imported else ['has_dynamic_data']
        has_high_value_data = []
        if is_enabled('S35_high_value_data.be'):
            has_high_value_data = ['has_high_value_data_info'] if obj and obj.is_imported else ['has_high_value_data']
        has_research_data = []
        if is_enabled('S47_research_data.be'):
            has_research_data = ['has_research_data_info'] if obj and obj.is_imported else ['has_research_data']
        general_fields = [
            'notes',
            'url',
            'image',
            'image_alt',
            'dataset_logo',
            'customfields',
            *has_dynamic_data,
            update_frequency_field,
            *frequency_fields,
            'organization',
            category_field,
            *has_high_value_data,
            *has_research_data,
        ]
        if is_enabled('S41_resource_bulk_download.be'):
            general_fields += ['archived_resources_files_media_url']
        general_fields += ['status', 'created_by', 'created', 'modified', 'verified']

        return [
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-general',),
                    'fields': (
                        'title',
                        'slug',
                    )
                }
            ),
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-tags',),
                    'fields': tags_tab_fields,
                }
            ),
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-general',),
                    'fields': general_fields
                }
            ),
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-licenses',),
                    'fields': (
                        'license_condition_source',
                        'license_condition_modification',
                        'license_condition_responsibilities',
                        'license_condition_cc40_responsibilities',
                        'license_condition_db_or_copyrighted',
                        'license_chosen',
                        'license_condition_personal_data',
                    ),
                }
            )
        ] + self.get_translations_fieldsets()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        archived_resources = ['archived_resources_files_media_url'] if is_enabled('S41_resource_bulk_download.be') else []
        readonly_fields = archived_resources + readonly_fields
        return readonly_fields

    def categories_list(self, instance):
        return instance.categories_list_as_html
    categories_list.short_description = _('Categories')

    def tags_list_pl(self, instance):
        return instance.tags_as_str(lang='pl')
    tags_list_pl.short_description = _('Tags') + ' (PL)'

    def tags_list_en(self, instance):
        return instance.tags_as_str(lang='en')
    tags_list_en.short_description = _('Tags') + ' (EN)'

    def get_search_results(self, request, queryset, search_term):
        if request.path == '/datasets/dataset/autocomplete/':
            queryset = queryset.filter(source__isnull=True)
        return super().get_search_results(request, queryset, search_term)

    def get_dataset_details(self, request, object_id):
        if not self.has_change_permission(request):
            raise PermissionDenied
        obj = Dataset.objects.filter(id=object_id).first()
        data = {
            'has_high_value_data': obj.has_high_value_data,
            'has_dynamic_data': obj.has_dynamic_data,
            'has_research_data': obj.has_research_data,
        } if obj else {}
        return JsonResponse(data)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/details/', self.get_dataset_details,
                 name='dataset-details')
        ] if is_enabled('S41_resource_has_high_value_data.be') else []
        return custom_urls + urls

    def render_change_form(self, request, context, **kwargs):
        obj = kwargs.get('obj')
        if obj and obj.source:
            context.update({
                'show_save': False,
                'show_save_and_continue': False,
            })
        return super().render_change_form(request, context, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        if not request.user.is_superuser:
            obj.update_notification_recipient_email = request.user.email
            if obj.tracker.has_changed('update_frequency'):
                obj.update_notification_frequency = UPDATE_NOTIFICATION_FREQUENCY_DEFAULT_VALUES.get(obj.update_frequency)

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.id:
                instance.created_by = request.user
            instance.modified_by = request.user
        super().save_formset(request, form, formset, change)

    def get_form(self, request, obj=None, **kwargs):
        self._request = request
        form = super().get_form(request, obj, **kwargs)
        form.recreate_tags_widgets(request=request, db_field=Dataset.tags.field, admin_site=self.admin_site)
        return form

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(organization_id__in=request.user.organizations.all())

    def has_history_permission(self, request, obj):
        return request.user.is_superuser or request.user.is_editor_of_organization(obj.organization)

    def dataset_logo(self, obj):
        return obj.dataset_logo or '-'
    dataset_logo.short_description = _('Logo')

    class Media:  # Empty media class is required if you are using autocomplete filter
        pass  # If you know better solution for altering admin.media from filter instance

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        formfield = super().formfield_for_manytomany(db_field, request, **kwargs)

        if db_field.name == "categories":
            attrs = {
                'data-from-box-label': _('Available categories'),
                'data-to-box-label': _('Selected categories'),
            }
            formfield.widget = admin.widgets.RelatedFieldWidgetWrapper(
                FilteredSelectMultipleCustom(formfield.label.lower(), False, attrs=attrs),
                db_field.remote_field,
                self.admin_site,
                can_add_related=False,
            )

        return formfield


@admin.register(DatasetTrash)
class DatasetTrashAdmin(HistoryMixin, TrashMixin):
    search_fields = ['title', 'organization__title']
    list_display = ['title', 'organization']
    related_objects_query = 'organization'
    cant_restore_msg = _(
        'Couldn\'t restore following datasets, because their related organizations are still removed: {}')
    fields = [
        'title',
        'slug',
        "notes",
        "url",
        "customfields",
        "update_frequency",
        'organization',
        'categories_list',
    ]

    license_fields = (
        "license_condition_source",
        "license_condition_modification",
        "license_condition_responsibilities",
        "license_condition_cc40_responsibilities",
        "license_condition_db_or_copyrighted",
        "license_chosen",
        "license_condition_personal_data",
    )

    fields += [
        'status',
        'tags_list_pl',
        'tags_list_en',
        *license_fields,
        "image",
        "image_alt",
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
        'categories_list',
        'status',
        'tags_list_pl',
        'tags_list_en',
        *license_fields,
        "image",
        "image_alt",
    ]

    form = TrashDatasetForm
    is_history_with_unknown_user_rows = True

    def categories_list(self, instance):
        return instance.categories_list_as_html
    categories_list.short_description = _('Categories')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(organization_id__in=request.user.organizations.all())

    def tags_list_pl(self, instance):
        return instance.tags_as_str(lang='pl')
    tags_list_pl.short_description = _('Tags') + ' (PL)'

    def tags_list_en(self, instance):
        return instance.tags_as_str(lang='en')
    tags_list_en.short_description = _('Tags') + ' (EN)'
