from dal_admin_filters import AutocompleteFilter
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.views.main import ChangeList
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db.models import Subquery, OuterRef
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult

from mcod.datasets.forms import DatasetForm, TrashDatasetForm, UPDATE_FREQUENCY
from mcod.datasets.models import Dataset, DatasetTrash
from mcod.lib.admin_mixins import (
    AddChangeMixin,
    AdminListMixin,
    HistoryMixin,
    LangFieldsOnlyMixin,
    SoftDeleteMixin,
    TrashMixin,
    CreatedByDisplayAdminMixin,
    ModifiedByDisplayAdminMixin,
    StatusLabelAdminMixin,
    DynamicAdminListDisplayMixin,
    MCODAdminMixin
)
from mcod.reports.admin import ExportCsvMixin
from mcod.resources.forms import ResourceListForm, AddResourceForm
from mcod.resources.models import Resource
from mcod.lib.dcat.vocabularies.manager import VocabulariesManager
from mcod.unleash import is_enabled
from mcod.users.forms import FilteredSelectMultipleCustom


class InlineChangeList(object):
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


class PaginationInline(admin.TabularInline):
    template = 'admin/resources/tabular_paginated.html'
    per_page = 20
    page_param = 'p'

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super(PaginationInline, self).get_formset(
            request, obj, **kwargs)

        class PaginationFormSet(formset_class):
            def __init__(self, *args, **kwargs):
                super(PaginationFormSet, self).__init__(*args, **kwargs)

                qs = self.queryset
                paginator = Paginator(qs, self.per_page)
                try:
                    page_num = int(request.GET.get(self.page_param, '0'))
                except ValueError:
                    page_num = 0

                try:
                    page = paginator.page(page_num + 1)
                except (EmptyPage, InvalidPage):
                    page = paginator.page(paginator.num_pages)

                self.cl = InlineChangeList(request, page_num, paginator, page_param=self.page_param)
                self.paginator = paginator

                if self.cl.show_all:
                    self._queryset = qs
                else:
                    self._queryset = page.object_list

        PaginationFormSet.per_page = self.per_page
        PaginationFormSet.page_param = self.page_param
        return PaginationFormSet


class ChangeResourceStacked(DynamicAdminListDisplayMixin, ModifiedByDisplayAdminMixin, StatusLabelAdminMixin,
                            AdminListMixin, PaginationInline):
    template = 'admin/resources/inline-list.html'
    show_change_link = True

    fields = (
        'title',
        'type',
        'formats',
        'link_status',
        'file_status',
        'data_status',
        'verified',
        'data_date',
        'modified',
        'modified_by',
        'status'
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

    def file_status(self, obj):
        return self._format_list_status(obj._file_status)

    file_status.admin_order_field = '_file_status'

    def data_status(self, obj):
        return self._format_list_status(obj._data_status)

    data_status.admin_order_field = '_data_status'

    if is_enabled('S21_admin_ui_changes.be'):
        data_status.short_description = format_html('<i class="fas fa-table" title="{}"></i>'.format(
            _('Tabular data validation status')))
        file_status.short_description = format_html('<i class="fas fa-file" title="{}"></i>'.format(
            _('File validation status')))
        link_status.short_description = format_html('<i class="fas fa-link" title="{}"></i>'.format(
            _('Link validation status')))
    else:
        data_status.short_description = format_html('<i class="fas fa-table"></i>')
        file_status.short_description = format_html('<i class="fas fa-file"></i>')
        link_status.short_description = format_html('<i class="fas fa-link"></i>')

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

    _fields = (
        'title',
        'description',
        'dataset',
        'data_date',
        'status',
    )
    if is_enabled('S16_special_signs.be'):
        _fields += ('special_signs', )
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


class OrganizationFilter(AutocompleteFilter):
    field_name = 'organization'  # field name - ForeignKey to Organization model
    autocomplete_url = 'organization-autocomplete'  # url name of Organization autocomplete view
    is_placeholder_title = False  # filter title will be shown as placeholder
    widget_attrs = {
        'data-placeholder': _('Filter by institution name')
    }


@admin.register(Dataset)
class DatasetAdmin(DynamicAdminListDisplayMixin, CreatedByDisplayAdminMixin, StatusLabelAdminMixin,
                   AddChangeMixin, SoftDeleteMixin, HistoryMixin, ExportCsvMixin, LangFieldsOnlyMixin,
                   MCODAdminMixin, admin.ModelAdmin):
    actions_on_top = True
    autocomplete_fields = ['tags', 'organization']
    list_display = ['title', 'organization', 'created', 'created_by', 'status', 'obj_history']
    readonly_fields = [
        'created_by',
        'created',
        'modified',
        'verified',
        'dataset_logo'
    ]
    inlines = [
        ChangeResourceStacked,
        AddResourceStacked,
    ]
    search_fields = ["title", ]
    prepopulated_fields = {
        "slug": ("title", ),
    }

    list_filter = []
    if is_enabled('S19_DCAT_categories.be'):
        list_filter += ['categories']
    else:
        list_filter += ['category']
    list_filter += [
        OrganizationFilter,
        'status'
    ]

    form = DatasetForm

    suit_form_tabs = (
        ('general', _('General')),
        *LangFieldsOnlyMixin.get_translations_tabs(),
        ('licenses', _('Conditions')),
        ('tags', _('Tags')),
        ('resources', _('Resources')),
    )

    suit_form_includes = (
        ('admin/datasets/licences/custom_include.html', 'top', 'licenses'),
    )

    def update_frequency_display(self, obj):
        if obj.update_frequency:
            return dict(UPDATE_FREQUENCY)[obj.update_frequency]

    update_frequency_display.short_description = _('Update frequency')

    def get_fieldsets(self, request, obj=None):
        if is_enabled('S18_new_tags.be'):
            tags_tab_fields = ('tags_list_pl', 'tags_list_en') if obj and obj.is_imported else ('tags_pl', 'tags_en')
        else:
            tags_tab_fields = ('tags_list', ) if obj and obj.is_imported else ('tags', )
        update_frequency_field = "update_frequency_display" if obj and obj.is_imported else "update_frequency"
        if is_enabled('dcat_vocabularies.be'):
            vocab_manager = VocabulariesManager('Dataset')
            vocabulary_choice_fields = vocab_manager.vocabularies
        else:
            vocabulary_choice_fields = []

        general_fields = ["notes", "url", "image", "image_alt", "dataset_logo", "customfields", update_frequency_field,
                          'organization']
        if is_enabled('S19_DCAT_categories.be'):
            general_fields += ['categories_list'] if obj and obj.is_imported else ['categories']
        else:
            general_fields += ['category']
        general_fields += vocabulary_choice_fields
        general_fields += ['status', 'created_by', 'created', 'modified', 'verified']

        if is_enabled('S21_licenses.be'):
            license_fields = (
                "license_condition_source",
                "license_condition_modification",
                "license_condition_responsibilities",
                "license_condition_db_or_copyrighted",
                "license_chosen",
                "license_condition_personal_data",
            )
        else:
            license_fields = (
                "license_condition_source",
                "license_condition_modification",
                "license_condition_responsibilities",
                "license_condition_db_or_copyrighted",
                "license_condition_personal_data",
            )

        return [
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-general',),
                    'fields': (
                        "title",
                        "slug",
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
                    'fields': license_fields,
                }
            )

        ] + self.get_translations_fieldsets()

    def categories_list(self, instance):
        return instance.categories_list_as_html
    categories_list.short_description = _('Categories')

    def tags_list(self, instance):
        return instance.tags_list_as_str
    tags_list.short_description = _('Tags')

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

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj and obj.source:
            context.update({
                'show_save': False,
                'show_save_and_continue': False,
            })
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        if is_enabled('dcat_vocabularies.be'):
            vocab_manager = VocabulariesManager('Dataset')
            obj.dcat_vocabularies =\
                vocab_manager.update_object_vocabularies(obj.dcat_vocabularies, form.changed_data, form.cleaned_data)
        super(DatasetAdmin, self).save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.id:
                instance.created_by = request.user
            instance.modified_by = request.user
        super(DatasetAdmin, self).save_formset(request, form, formset, change)

    def get_form(self, request, obj=None, **kwargs):
        self._request = request
        form = super(DatasetAdmin, self).get_form(request, obj, **kwargs)
        if is_enabled('dcat_vocabularies.be') and obj:
            VocabulariesManager.set_vocabulary_fields_initial(form, obj)
        if is_enabled('S18_new_tags.be'):
            form.recreate_tags_widgets(request=request, db_field=Dataset.tags.field, admin_site=self.admin_site)
        return form

    def get_queryset(self, request):
        qs = Dataset.objects.all()

        if request.user.is_superuser:
            return qs
        return qs.filter(organization_id__in=request.user.organizations.all())

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
    ]
    if is_enabled('S19_DCAT_categories.be'):
        fields += ['categories_list']
    else:
        fields += ['category']

    if is_enabled('S18_new_tags.be'):
        tags_fields = ('tags_list_pl', 'tags_list_en')
    else:
        tags_fields = ('tags',)

    if is_enabled('S21_licenses.be'):
        license_fields = (
            "license_condition_source",
            "license_condition_modification",
            "license_condition_responsibilities",
            "license_condition_db_or_copyrighted",
            "license_chosen",
            "license_condition_personal_data",
        )
    else:
        license_fields = (
            "license_id",
            "license_condition_source",
            "license_condition_original",
            "license_condition_modification",
            "license_condition_responsibilities",
            "license_condition_db_or_copyrighted",
            "license_condition_personal_data",
        )

    fields += [
        'status',
        *tags_fields,
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
    ]
    if is_enabled('S19_DCAT_categories.be'):
        readonly_fields += ['categories_list']
    else:
        readonly_fields += ['category']

    readonly_fields += [
        'status',
        *tags_fields,
        *license_fields,
        "image",
        "image_alt",
    ]

    form = TrashDatasetForm

    def categories_list(self, instance):
        return instance.categories_list_as_html
    categories_list.short_description = _('Categories')

    def get_queryset(self, request):
        qs = Dataset.deleted.all()
        if request.user.is_superuser:
            return qs
        return qs.filter(organization_id__in=request.user.organizations.all())

    def tags_list_pl(self, instance):
        return instance.tags_as_str(lang='pl')
    tags_list_pl.short_description = _('Tags') + ' (PL)'

    def tags_list_en(self, instance):
        return instance.tags_as_str(lang='en')
    tags_list_en.short_description = _('Tags') + ' (EN)'
