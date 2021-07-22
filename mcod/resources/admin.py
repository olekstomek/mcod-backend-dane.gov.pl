from dal_admin_filters import AutocompleteFilter
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, FieldDoesNotExist
from django.db.models import Subquery, OuterRef, ManyToManyField
from django.forms.models import model_to_dict
from django.http.response import HttpResponseRedirect, Http404
from django.template.loader import get_template
from django.urls import reverse, path
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult

from mcod.lib.admin_mixins import (
    AddChangeMixin, AdminListMixin, TrashMixin, HistoryMixin,
    LangFieldsOnlyMixin, SoftDeleteMixin, StatusLabelAdminMixin, DynamicAdminListDisplayMixin, MCODAdminMixin
)
from mcod.lib.helpers import get_paremeters_from_post
from mcod.reports.admin import ExportCsvMixin
from mcod.resources.forms import ChangeResourceForm, AddResourceForm, TrashResourceForm
from mcod.resources.models import (
    Resource, ResourceTrash, RESOURCE_TYPE_WEBSITE, RESOURCE_TYPE,
    RESOURCE_TYPE_API_CHANGE_LABEL, RESOURCE_TYPE_API_CHANGE, RESOURCE_TYPE_API
)
from mcod.unleash import is_enabled


rules_names = {x[0]: x[1] for x in settings.VERIFICATION_RULES}


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


class TypeFilter(admin.SimpleListFilter):
    title = _('Type')
    parameter_name = 'type'
    qs_param = '_type'

    def lookups(self, request, model_admin):
        return (
            *RESOURCE_TYPE,
            (RESOURCE_TYPE_API_CHANGE, RESOURCE_TYPE_API_CHANGE_LABEL),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        if value == RESOURCE_TYPE_API_CHANGE:
            return queryset.filter(type=RESOURCE_TYPE_API, forced_api_type=True)

        return queryset.filter(type=value).exclude(forced_api_type=True)


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


def get_colname(col, table_schema):
    fields = table_schema.get('fields')
    col_index = int(col.replace("col", "")) - 1
    return fields[col_index]['name']


def process_verification_results(col, results, table_schema, rules):

    def get_result(data, col):
        val = data.get(col, '')
        val = val.get('val', '') if isinstance(val, dict) and 'val' in val else val
        return data['row_no'], val or ''

    msg_class = messages.ERROR
    colname = get_colname(col, table_schema)
    results_hits = results.get('hits')
    translated_rule_name = rules_names.get(rules[col])
    if results_hits:
        hits = results_hits.get('hits')
        if len(hits) > 0:
            template = get_template('admin/resources/message_template.html')
            output = template.render(
                {
                    'results': [get_result(h['_source'], col) for h in hits],
                    'colname': colname,
                    'rule': translated_rule_name,
                }
            )
        else:
            msg_class = messages.SUCCESS
            text = _('During the verification of column "{colname}" with the "{rule}" rule no errors detected').format(
                colname=colname, rule=translated_rule_name)
            output = f'''<span>{text}</span>'''
    else:
        text = _('Verification of column "{colname}" by the rule "{rule}" failed').format(
            colname=colname, rule=translated_rule_name)

        output = f'''<span>{text}</span>'''

    return mark_safe(output), msg_class


@admin.register(Resource)
class ResourceAdmin(DynamicAdminListDisplayMixin, AddChangeMixin, StatusLabelAdminMixin, AdminListMixin, SoftDeleteMixin,
                    HistoryMixin, ExportCsvMixin, LangFieldsOnlyMixin, MCODAdminMixin, admin.ModelAdmin):
    actions_on_top = True

    if is_enabled('S22_forced_api_type.be'):
        TYPE_FILTER = TypeFilter
        TYPE_DISPLAY_FIELD = 'type_as_str'
    else:
        TYPE_FILTER = 'type'
        TYPE_DISPLAY_FIELD = 'type'

    def change_suit_form_tabs(self, obj):
        form_tabs = [
            ('general', _('General')),
            *LangFieldsOnlyMixin.get_translations_tabs(),
            ('file', _('File validation')),
            ('link', _('Link validation')),
            ('data', _('Data validation')),

        ]

        if obj.tabular_data_schema and obj.format != 'shp':
            form_tabs.append(('types', _("Change of type")))

        resource_validation_tab = ('rules', _('Quality verification'), 'disabled')

        if (settings.RESOURCE_VALIDATION_TOOL_ENABLED
                and obj.tabular_data_schema
                and obj.format != 'shp'
                and obj.has_data):
            resource_validation_tab = ('rules', _('Quality verification'))

        form_tabs.append(resource_validation_tab)

        maps_and_plots_tab = ("maps_and_plots", _("Maps and plots"), 'disabled')
        if obj.tabular_data_schema:
            maps_and_plots_tab = ("maps_and_plots", _("Maps and plots"))
        form_tabs.append(maps_and_plots_tab)

        return form_tabs

    add_suit_form_tabs = (
        ('general', _('General')),
        *LangFieldsOnlyMixin.get_translations_tabs()
    )

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
            'fields': ('status', 'from_resource'),
        }),
    ]
    if is_enabled('S16_special_signs.be'):
        add_fieldsets.append(
            (None, {
                'classes': ('suit-tab', 'suit-tab-general'),
                'fields': ('special_signs', ),
            })
        )

    change_readonly_fields = (
        'formats',
        'file',
        'csv_file',
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
        'formats',
        'dataset',
        'status',
        TYPE_DISPLAY_FIELD,
        'link_status',
        'file_status',
        'tabular_view',
        'created',
    ]

    list_filter = [
        DatasetFilter,
        "format",
        TYPE_FILTER,
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
        LinkTaskResultInline,
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'dataset':
            kwargs['queryset'] = db_field.remote_field.model._default_manager.filter(source__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_imported:
            return True  # required to display content in "data validation tabs" properly.
        return super().has_change_permission(request, obj=obj)

    def tabular_data_rules_fieldset(self, obj):
        fieldsets = []
        if obj.has_data:
            fieldsets = [(
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-rules', 'full-width'),
                    'fields': (
                        'data_rules',
                    )
                }
            ), ]
        return fieldsets

    def tabular_data_schema_fieldset(self, obj):
        fieldsets = []
        if obj.tabular_data_schema:
            fieldsets = [(
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-types', 'full-width'),
                    'fields': (
                        'tabular_data_schema',
                    )
                }
            ), ]
        return fieldsets

    def maps_and_plots_fieldset(self, obj):
        if is_enabled('S24_named_charts.be'):
            fields = ('maps_and_plots', 'is_chart_creation_blocked', )
        else:
            fields = ('maps_and_plots', )
        fieldsets = [(
            None,
            {
                'classes': ('suit-tab', 'suit-tab-maps_and_plots', 'full-width'),
                'fields': fields,
            }
        ), ]
        return fieldsets if obj.tabular_data_schema else []

    def get_fieldsets(self, request, obj=None):
        if obj:
            extra_fields = []
            if is_enabled('S22_forced_api_type.be') and (obj.type == RESOURCE_TYPE_WEBSITE or obj.forced_api_type):
                extra_fields = ['forced_api_type']

            tab_general_fields = (
                'link',
                *extra_fields,
                'file',
                'csv_file',
                'packed_file',
                'title',
                'description',
                'formats',
                'dataset',
                'data_date',
                'status',
                'special_signs',
                'show_tabular_view',
                'modified',
                'created',
                'verified',
                'type',
                'file_info',
                'file_encoding',
            )
            if obj.is_imported:
                tab_general_fields = (x for x in tab_general_fields if x != 'special_signs')
            if not is_enabled('S16_special_signs.be'):
                tab_general_fields = (x for x in tab_general_fields if x != 'special_signs')
            if not obj.csv_file:
                tab_general_fields = (x for x in tab_general_fields if x != 'csv_file')
            change_fieldsets = [
                (
                    None,
                    {
                        'classes': ('suit-tab', 'suit-tab-general',),
                        'fields': tab_general_fields,
                    }
                ),
            ]
            fieldsets = (
                change_fieldsets +
                self.tabular_data_rules_fieldset(obj) +
                self.tabular_data_schema_fieldset(obj) +
                self.maps_and_plots_fieldset(obj)
            )
        else:
            fieldsets = tuple(self.add_fieldsets)

        fieldsets += tuple(self.get_translations_fieldsets())

        return fieldsets

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
        if obj and not obj.data_is_valid:
            readonly_fields = (*readonly_fields, 'show_tabular_view')
        if obj and obj.type != "file":
            readonly_fields = (*readonly_fields, 'data_date')
        if obj and obj.is_imported:
            readonly_fields = (
                *readonly_fields, 'dataset', 'data_date', 'description', 'description_en', 'show_tabular_view',
                'slug_en', 'status', 'title', 'title_en', 'is_chart_creation_blocked')
        return tuple(set(readonly_fields))

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context.update(
            {
                'suit_form_tabs': self.change_suit_form_tabs(obj) if obj else self.add_suit_form_tabs
            }
        )
        if obj and obj.is_imported:
            context.update({
                'show_save': False,
                'show_save_and_continue': False,
            })
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

    def link_status(self, obj):
        return self._format_list_status(obj._link_status)

    link_status.admin_order_field = '_link_status'

    def file_status(self, obj):
        return self._format_list_status(obj._file_status)

    file_status.admin_order_field = '_file_status'

    def formats(self, obj):
        return obj.formats or '-'

    formats.admin_order_field = 'format'
    formats.short_description = 'Format'

    def tabular_view(self, obj):
        return self._format_list_status(obj._data_status)

    tabular_view.admin_order_field = '_data_status'

    if is_enabled('S21_admin_ui_changes.be'):
        tabular_view.short_description = format_html('<i class="fas fa-table" title="{}"></i>'.format(
            _('Tabular data validation status')))
        file_status.short_description = format_html('<i class="fas fa-file" title="{}"></i>'.format(
            _('File validation status')))
        link_status.short_description = format_html('<i class="fas fa-link" title="{}"></i>'.format(
            _('Link validation status')))
    else:
        tabular_view.short_description = format_html('<i class="fas fa-table"></i>')
        file_status.short_description = format_html('<i class="fas fa-file"></i>')
        link_status.short_description = format_html('<i class="fas fa-link"></i>')

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
            try:
                origin = Resource.objects.get(pk=obj_id)
            except Resource.DoesNotExist:
                origin = None
            if origin and not origin.is_imported:  # making a copy of resource is disabled for imported resources.
                data = model_to_dict(origin)
                initial['title'] = data.get('title')
                initial['description'] = data.get('description')
                initial['status'] = data.get('status')
                initial['dataset'] = data.get('dataset')
                initial['from_resource'] = origin
                initial['title_en'] = data.get('title_en')
                initial['description_en'] = data.get('description_en')
                initial['slug_en'] = data.get('slug_en')

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

    def response_change(self, request, obj):

        if '_verify_rules' in request.POST:
            rules = get_paremeters_from_post(request.POST)
            results = obj.verify_rules(rules)
            for col, res in results.items():
                res, msg_class = process_verification_results(col, res, obj.tabular_data_schema, rules)
                self.message_user(request, res, msg_class)
            return HttpResponseRedirect(".")

        elif '_change_type' in request.POST:
            obj.save()
            messages.add_message(request, messages.SUCCESS, _('Data type changed'))
            self.revalidate(request, obj.id)

        elif '_map_save' in request.POST:
            obj.save()
            messages.add_message(request, messages.SUCCESS, _('Map definition saved'))
            self.revalidate(request, obj.id)
            # add here another actions

        return super().response_change(request, obj)

    def _changeform_view(self, request, object_id, form_url, extra_context):
        if '_validate_rules' in request.POST:
            obj = self.model.objects.get(pk=object_id)
            return self.response_change(request, obj)
        else:
            return super()._changeform_view(request, object_id, form_url, extra_context)


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
    readonly_fields = [field for field in fields if field != 'is_removed']

    form = TrashResourceForm

    def get_queryset(self, request):
        qs = Resource.deleted.all()
        if request.user.is_superuser:
            return qs
        return qs.filter(dataset__organization_id__in=request.user.organizations.all())
