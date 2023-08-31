from dal_admin_filters import AutocompleteFilter
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http.response import HttpResponseRedirect
from django.template.defaultfilters import truncatewords, yesno
from django.template.loader import get_template
from django.urls import path
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)

from mcod.datasets.admin import OrganizationFilter
from mcod.histories.models import LogEntry
from mcod.lib.admin_mixins import HistoryMixin, ModelAdmin, SortableStackedInline, TrashMixin
from mcod.lib.helpers import get_paremeters_from_post
from mcod.organizations.models import Organization
from mcod.resources.forms import (
    AddResourceForm,
    ChangeResourceForm,
    SupplementForm,
    TrashResourceForm,
)
from mcod.resources.models import (
    RESOURCE_FORCED_TYPE,
    RESOURCE_TYPE,
    RESOURCE_TYPE_API,
    RESOURCE_TYPE_API_CHANGE,
    RESOURCE_TYPE_FILE,
    RESOURCE_TYPE_FILE_CHANGE,
    RESOURCE_TYPE_WEBSITE,
    Resource,
    ResourceFile,
    ResourceTrash,
    Supplement,
    supported_formats_choices,
)

rules_names = {x[0]: x[1] for x in settings.VERIFICATION_RULES}


class DatasetFilter(AutocompleteFilter):
    autocomplete_url = 'dataset-autocomplete'
    field_name = 'dataset'
    is_placeholder_title = True
    title = _('Filter by dataset name')


class ResourceOrganizationFilter(OrganizationFilter):
    field_name = 'organization'
    parameter_name = 'dataset__organization'

    def get_queryset_for_field(self, model, name):
        return Organization.objects.all()


class FormatFilter(admin.SimpleListFilter):
    parameter_name = 'format'
    title = 'Format'

    def lookups(self, request, model_admin):
        return supported_formats_choices(with_archives=True)

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset
        query = Q(format=val) | Q(files__format=val)
        return queryset.filter(query).distinct()


class TaskStatus(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        return (
            ('SUCCESS', _('Correct Validation')),
            ('FAILURE', _('Validation failed')),
            ('PENDING', _('Validation in progress')),
            ('N/A', _('No validation'))
        )

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset
        val = '' if val == 'N/A' else val
        return queryset.filter(**{self.qs_param: val})


class TypeFilter(admin.SimpleListFilter):
    title = _('Type')
    parameter_name = 'type'
    qs_param = '_type'

    def lookups(self, request, model_admin):
        return (
            *RESOURCE_TYPE,
            *RESOURCE_FORCED_TYPE,
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        if value == RESOURCE_TYPE_API_CHANGE:
            return queryset.filter(type=RESOURCE_TYPE_API, forced_api_type=True)
        elif value == RESOURCE_TYPE_FILE_CHANGE:
            return queryset.filter(type=RESOURCE_TYPE_FILE, forced_file_type=True)
        return queryset.filter(type=value).exclude(
            Q(forced_api_type=True) | Q(forced_file_type=True))


class LinkStatusFilter(TaskStatus):
    title = _('Link status')
    parameter_name = 'link_status'
    qs_param = 'link_tasks_last_status'


class FileStatusFilter(TaskStatus):
    title = _('File status')
    parameter_name = 'file_status'
    qs_param = 'file_tasks_last_status'


class TabularViewFilter(TaskStatus):
    title = _('TabularView')
    parameter_name = 'tabular_view_status'
    qs_param = 'data_tasks_last_status'


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


class SupplementInline(SortableStackedInline):
    add_text = _('Add document')
    fields = ['file', 'name', 'name_en', 'language']
    form = SupplementForm
    description = 'Pliki dokumentów mające na celu uzupełnienie danych znajdujących się w zasobie.'
    extra = 0
    max_num = 10
    model = Supplement
    suit_classes = 'suit-tab suit-tab-supplements js-inline-admin-formset'
    suit_form_inlines_hide_original = True
    verbose_name = _('document')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_imported:
            return ['name', 'name_en', 'file']
        return super().get_readonly_fields(request, obj=obj)

    def has_add_permission(self, request, obj=None):
        if obj and obj.is_imported:
            return False
        return super().has_add_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_imported:
            return False
        return super().has_delete_permission(request, obj=obj)


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
    translated_rule_name = rules_names.get(rules[col], rules[col])
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
class ResourceAdmin(HistoryMixin, ModelAdmin):
    actions_on_top = True
    check_imported_obj_perms = True
    export_to_csv = True
    lang_fields = True
    soft_delete = True
    TYPE_FILTER = TypeFilter
    is_inlines_js_upgraded = True

    def get_suit_form_tabs(self, obj=None):
        tabs = [
            ('general', _('General')),
            *self.get_translations_tabs(),
        ]
        if obj:
            tabs.extend([
                ('file', _('File validation')),
                ('link', _('Link validation')),
                ('data', _('Data validation')),
            ])
            if obj.tabular_data_schema and obj.format != 'shp':
                tabs.append(('types', _("Change of type")))
            resource_validation_tab = ('rules', _('Quality verification'), 'disabled')

            if (settings.RESOURCE_VALIDATION_TOOL_ENABLED
                    and obj.tabular_data_schema
                    and obj.format != 'shp'
                    and obj.has_data):
                resource_validation_tab = ('rules', _('Quality verification'))
            tabs.append(resource_validation_tab)

            maps_and_plots_tab = ("maps_and_plots", _("Maps and plots"), 'disabled')
            if obj.tabular_data_schema:
                maps_and_plots_tab = ("maps_and_plots", _("Maps and plots"))
            tabs.append(maps_and_plots_tab)
        tabs.append(('supplements', _('Supplements')))
        return tabs

    list_display = [
        'title',
        'lang',
        'formats',
        'dataset',
        'status_label',
        'type_as_str',
        'link_status',
        'file_status',
        'tabular_view',
        'created',
    ]

    list_filter = [
        ResourceOrganizationFilter,
        DatasetFilter,
        FormatFilter,
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
        SupplementInline,
    ]
    suit_form_includes = (
        ('widgets/resource_data_types_actions.html', 'bottom', 'types'),
        ('widgets/resource_data_rules_actions.html', 'bottom', 'rules'),
        ('widgets/resource_maps_and_plots_actions.html', 'bottom', 'maps_and_plots'),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'dataset':
            kwargs['queryset'] = db_field.remote_field.model._default_manager.filter(source__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_imported:
            return True  # required to display content in "data validation tabs" properly.
        return super().has_change_permission(request, obj=obj)

    def get_fieldsets(self, request, obj=None):
        if obj:
            jsonld_file = ['jsonld_converted_file'] if obj.jsonld_converted_file else []
            file = ['main_file']
            csv_file = ['csv_converted_file'] if obj.csv_converted_file else []
            special_signs = ['special_signs'] if not obj.is_imported else ['special_signs_symbols']
            file_info = ['main_file_info']
            file_encoding = ['main_file_encoding']
            regions = ['regions'] if not obj.is_imported else []
            has_dynamic_data = ['has_dynamic_data'] if not obj.is_imported else ['has_dynamic_data_info']
            has_high_value_data = ['has_high_value_data'] if not obj.is_imported else ['has_high_value_data_info']
            has_research_data = ['has_research_data'] if not obj.is_imported else ['has_research_data_info']
            extra_fields = []
            if obj.type == RESOURCE_TYPE_WEBSITE or obj.forced_api_type:
                extra_fields = ['forced_api_type']
            elif not obj.forced_api_type and (
                    obj.type == RESOURCE_TYPE_API or obj.forced_file_type or
                    (obj.type == RESOURCE_TYPE_FILE and obj.tracker.has_changed('forced_file_type'))):
                extra_fields = ['forced_file_type']
            show_dd_update_fields = (obj.is_auto_data_date_allowed and
                                     not obj.is_imported)
            dd_update_fields = [
                'is_auto_data_date',
                'automatic_data_date_start',
                'data_date_update_period',
                'automatic_data_date_end',
                'endless_data_date_update'
            ] if show_dd_update_fields else []
            extra_fields = extra_fields if not obj.is_imported else []
            fieldsets = [
                (
                    None,
                    {
                        'classes': ('suit-tab', 'suit-tab-general',),
                        'fields': (
                            'link',
                            *extra_fields,
                            *file,
                            *csv_file,
                            *jsonld_file,
                            'packed_file',
                            'language',
                            'title',
                            'description',
                            'formats',
                            'dataset',
                            *regions,
                            'related_resource',
                            'data_date',
                            *dd_update_fields,
                            *has_dynamic_data,
                            *has_high_value_data,
                            *has_research_data,
                            'status',
                            *special_signs,
                            'show_tabular_view',
                            'modified',
                            'created',
                            'verified',
                            'type',
                            *file_info,
                            *file_encoding,
                        ),
                    }
                ),
            ]
            if obj.has_data:
                fieldsets.append(
                    (
                        None,
                        {
                            'classes': ('suit-tab', 'suit-tab-rules', 'full-width'),
                            'fields': (
                                'data_rules',
                            )
                        }
                    )
                )
            if obj.tabular_data_schema:
                fieldsets.extend(
                    [
                        (
                            None,
                            {
                                'classes': ('suit-tab', 'suit-tab-types', 'full-width'),
                                'fields': (
                                    'tabular_data_schema',
                                )
                            }
                        ),
                        (
                            None,
                            {
                                'classes': ('suit-tab', 'suit-tab-maps_and_plots', 'full-width'),
                                'fields': ('maps_and_plots', 'is_chart_creation_blocked',),
                            }
                        )
                    ]
                )
        else:
            fieldsets = tuple([
                (None, {
                    'classes': ('suit-tab', 'suit-tab-general'),
                    'fields': (
                        'switcher',
                        'file',
                        'link',
                        'language',
                    ),
                }),
                (None, {
                    'classes': ('suit-tab', 'suit-tab-general'),
                    'fields': ('title', 'description'),
                }),
                (None, {
                    'classes': ('suit-tab', 'suit-tab-general'),
                    'fields': (
                        'dataset',
                        'regions',
                        'related_resource',
                    ),
                }),
                (None, {
                    'classes': ('suit-tab', 'suit-tab-general'),
                    'fields': ('data_date',),
                }),
                (None, {
                    'classes': ('suit-tab', 'suit-tab-general'),
                    'fields': ('has_dynamic_data',),
                }),
                (None, {
                    'classes': ('suit-tab', 'suit-tab-general'),
                    'fields': ('has_high_value_data',),
                }),
                (None, {
                    'classes': ('suit-tab', 'suit-tab-general'),
                    'fields': ('has_research_data',),
                }),
                (None, {
                    'classes': ('suit-tab', 'suit-tab-general'),
                    'fields': ('status', 'from_resource'),
                }),
                (None, {
                    'classes': ('suit-tab', 'suit-tab-general'),
                    'fields': ('special_signs',),
                })
            ])

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

    def get_history(self, obj):
        history = super().get_history(obj)
        supplements = Supplement.raw.filter(resource=obj)
        supplements_history = LogEntry.objects.get_for_objects(supplements)
        all_history = history.distinct() | supplements_history
        return all_history.order_by('-timestamp')

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = (
            'formats',
            'file',
            'csv_file',
            'jsonld_file',
            'packed_file',
            'link',
            'modified',
            'created',
            'verified',
            'type',
            'file_info',
            'file_encoding',
            'special_signs_symbols',
            'link_tasks',
            'file_tasks',
            'data_tasks',
        ) if obj and obj.id else ()
        new_fields_mapping = {
            'file': 'main_file',
            'file_info': 'main_file_info',
            'file_encoding': 'main_file_encoding',
            'csv_file': 'csv_converted_file',
            'jsonld_file': 'jsonld_converted_file'
        }
        readonly_fields = [
            field if field not in new_fields_mapping else new_fields_mapping[field]
            for field in readonly_fields
        ]
        if obj and not obj.data_is_valid:
            readonly_fields = (*readonly_fields, 'show_tabular_view')
        if obj and obj.is_imported:
            auto_data_date_fields = [
                'is_auto_data_date_info',
                'automatic_data_date_start',
                'data_date_update_period',
                'automatic_data_date_end',
                'endless_data_date_update'
            ] if obj.is_auto_data_date else ['is_auto_data_date_info']
            readonly_fields = (
                *readonly_fields,
                'dataset',
                'data_date',
                *auto_data_date_fields,
                'description',
                'description_en',
                'show_tabular_view',
                'slug_en',
                'status',
                'title',
                'title_en',
                'is_chart_creation_blocked',
                'has_dynamic_data_info',
                'has_high_value_data_info',
                'has_research_data_info',
                'language',
                'related_resource',
            )
        return tuple(set(readonly_fields))

    def lang(self, obj):
        return obj.get_language_display()
    lang.short_description = _('data language')
    lang.admin_order_field = 'language'

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        extra = {
            'suit_form_tabs': self.get_suit_form_tabs(obj=obj),
        }
        if obj and obj.is_imported:
            extra['show_save'] = False
            extra['show_save_and_continue'] = False
        media = context.get('media')
        if media and self.is_inlines_js_upgraded:
            _new_js_lists = []
            for js_list in media._js_lists:
                new_js_list = [x for x in js_list if x not in ['admin/js/inlines.min.js', 'admin/js/inlines.js']]
                if len(new_js_list) < len(js_list):
                    new_js_list.append('admin/js/inlines_django_3_1.js')
                _new_js_lists.append(new_js_list)
            media._js_lists = _new_js_lists
            context['media'] = media
        context.update(extra)
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_staff and not request.user.is_superuser:
            qs = qs.filter(dataset__organization__in=request.user.organizations.iterator())
        return qs

    def link_status(self, obj):
        return self._format_list_status(obj.link_tasks_last_status)

    link_status.admin_order_field = 'link_tasks_last_status'

    def file_status(self, obj):
        return self._format_list_status(obj.file_tasks_last_status)

    file_status.admin_order_field = 'file_tasks_last_status'

    def formats(self, obj):
        return obj.formats or '-'

    formats.admin_order_field = 'format'
    formats.short_description = 'Format'

    def has_dynamic_data_info(self, obj):
        return yesno(obj.has_dynamic_data, 'Tak,Nie,-')
    has_dynamic_data_info.short_description = _('dynamic data')

    def has_high_value_data_info(self, obj):
        return yesno(obj.has_high_value_data, 'Tak,Nie,-')
    has_high_value_data_info.short_description = _('has high value data')

    def has_research_data_info(self, obj):
        return yesno(obj.has_research_data, 'Tak,Nie,-')
    has_research_data_info.short_description = _('has research data')

    def is_auto_data_date_info(self, obj):
        return yesno(obj.is_auto_data_date, 'Tak,Nie,-')
    is_auto_data_date_info.short_description = _('Manual update')

    def special_signs_symbols(self, obj):
        return obj.special_signs_symbols or '-'
    special_signs_symbols.short_description = _('Special Signs')

    def tabular_view(self, obj):
        return self._format_list_status(obj.data_tasks_last_status)

    tabular_view.admin_order_field = 'data_tasks_last_status'

    tabular_view.short_description = format_html('<i class="fas fa-table" title="{}"></i>'.format(
        _('Tabular data validation status')))
    file_status.short_description = format_html('<i class="fas fa-file" title="{}"></i>'.format(
        _('File validation status')))
    link_status.short_description = format_html('<i class="fas fa-link" title="{}"></i>'.format(
        _('Link validation status')))

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Supplement):
                if not instance.id:
                    instance.created_by = request.user
                instance.modified_by = request.user
        super().save_formset(request, form, formset, change)

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        if obj.file:
            obj.file = None

        revalidate = False
        if change and obj.status == obj.STATUS.published:
            if (
                    obj.tracker.has_changed('tabular_data_schema')
                    or set(obj.special_signs.values_list('id')) != set(form.cleaned_data['special_signs'].values_list('id'))
            ):
                revalidate = True

            if obj.is_link_updated or obj.state_restored:
                # if this condition is met, revalidation will occur in resources.models.process_resource
                revalidate = False

        obj.save()

        if form.cleaned_data.get('file'):
            ResourceFile.objects.update_or_create(
                resource=obj,
                is_main=True,
                defaults={
                    'file': form.cleaned_data['file']
                }
            )

        if revalidate:
            obj.revalidate()

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
                initial['has_dynamic_data'] = data.get('has_dynamic_data')
                initial['has_high_value_data'] = data.get('has_high_value_data')
                initial['has_research_data'] = data.get('has_research_data')
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
            messages.add_message(request, messages.WARNING, _('Resource with this id does not exists'))
            return HttpResponseRedirect(self.model.admin_list_url())

        resource.revalidate()
        messages.add_message(request, messages.SUCCESS, _('Task for resource revalidation queued'))
        return HttpResponseRedirect(resource.admin_change_url)

    def response_change(self, request, obj):
        if '_verify_rules' in request.POST:
            rules = get_paremeters_from_post(request.POST)
            results = obj.verify_rules(rules)
            for col, res in results.items():
                res, msg_class = process_verification_results(col, res, obj.tabular_data_schema, rules)
                self.message_user(request, res, msg_class)
            return HttpResponseRedirect(".")
        elif '_change_type' in request.POST:
            messages.add_message(request, messages.SUCCESS, _('Data type changed'))
        elif '_map_save' in request.POST:
            messages.add_message(request, messages.SUCCESS, _('Map definition saved'))
        return super().response_change(request, obj)

    def _changeform_view(self, request, object_id, form_url, extra_context):
        if '_verify_rules' in request.POST:
            obj = self.model.objects.get(pk=object_id)
            return self.response_change(request, obj)
        else:
            return super()._changeform_view(request, object_id, form_url, extra_context)


@admin.register(ResourceTrash)
class TrashAdmin(HistoryMixin, TrashMixin):
    list_display = ['title_short', 'dataset', 'modified']
    search_fields = ['title', 'dataset__title']
    form = TrashResourceForm
    is_history_with_unknown_user_rows = True
    related_objects_query = 'dataset'
    cant_restore_msg = _(
        'Couldn\'t restore following resources, because their related datasets are still removed: {}')

    def title_short(self, obj):
        return truncatewords(obj.title, 18)
    title_short.short_description = _('Name')
    title_short.admin_order_field = 'title'

    def get_fields(self, request, obj=None):
        csv_file = ['csv_converted_file'] if obj and obj.csv_converted_file else []
        jsonld_file = ['jsonld_converted_file'] if obj and obj.jsonld_converted_file else []
        file = ['main_file'] if obj and obj.main_file else []
        return [
            *file,
            *csv_file,
            *jsonld_file,
            'link',
            'language',
            'title',
            'description',
            'dataset',
            'related_resource',
            'status',
            'created',
            'modified',
            'verified',
            'data_date',
            'is_removed',
        ]

    def get_readonly_fields(self, request, obj=None):
        return [field for field in self.get_fields(request, obj=obj) if field != 'is_removed']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(dataset__organization_id__in=request.user.organizations.all())


admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)
admin.site.unregister(PeriodicTask)
