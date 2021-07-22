from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from modeltrans.translator import get_i18n_field

from mcod import settings
from mcod.applications.forms import ApplicationForm, ApplicationProposalForm
from mcod.applications.models import Application, ApplicationProposal, ApplicationProposalTrash, ApplicationTrash
from mcod.applications.tasks import create_application_task
from mcod.lib.admin_mixins import (
    ActionsMixin,
    CRUDMessageMixin,
    DecisionFilter,
    HistoryMixin,
    LangFieldsOnlyMixin,
    SoftDeleteMixin,
    TrashMixin,
    CreatedByDisplayAdminMixin,
    DecisionStatusLabelAdminMixin,
    DynamicAdminListDisplayMixin,
    MCODAdminMixin
)
from mcod.reports.admin import ExportCsvMixin


@admin.register(Application)
class ApplicationAdmin(DynamicAdminListDisplayMixin, CreatedByDisplayAdminMixin, CRUDMessageMixin, SoftDeleteMixin,
                       HistoryMixin, LangFieldsOnlyMixin, MCODAdminMixin, admin.ModelAdmin):
    actions_on_top = True
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['tags']
    readonly_fields = ['application_logo', 'illustrative_graphics_img', 'preview_link']
    list_display = [
        'title',
        'created_by',
        'application_logo',
        'modified',
        'main_page_position',
        'status',
        'obj_history'
    ]
    obj_gender = 'f'
    search_fields = ['title', 'created_by__email', 'url']
    list_filter = ['status', 'main_page_position']
    list_editable = ['status']

    suit_form_tabs = (
        ('general', _('General')),
        *LangFieldsOnlyMixin.get_translations_tabs(),
        ('tags', _('Tags')),
        ('datasets', _('Datasets')),
    )

    form = ApplicationForm
    is_history_with_unknown_user_rows = True

    def get_translations_fieldsets(self):
        i18n_field = get_i18n_field(self.model)
        fieldsets = []
        for lang_code in settings.MODELTRANS_AVAILABLE_LANGUAGES:
            fields = [f'{field.name}' for field in i18n_field.get_translated_fields() if field.name.endswith(lang_code)]
            if lang_code == settings.LANGUAGE_CODE:
                continue
            tab_name = 'general' if lang_code == settings.LANGUAGE_CODE else f'lang-{lang_code}'
            fieldset = (None, {
                'classes': ('suit-tab', f'suit-tab-{tab_name}',),
                'fields': fields
            })
            fieldsets.append(fieldset)
        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.recreate_tags_widgets(request=request, db_field=Application.tags.field, admin_site=self.admin_site)
        return form

    def get_fieldsets(self, request, obj=None):
        tab_general_fields = (
            'notes',
            'author',
            'external_datasets',
            'url',
            'image',
            'image_alt',
            'application_logo',
            'illustrative_graphics',
            'illustrative_graphics_alt',
            'illustrative_graphics_img',
            'main_page_position',
            'status',
        )
        tab_general_fields2 = [
            'preview_link',
            'title',
        ]

        fieldsets = [
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-general',),
                    'fields': tab_general_fields2
                }
            ),
            (
                None,
                {
                    'classes': ('collapse', 'suit-tab', 'suit-tab-general',),
                    'fields': (
                        'slug',
                    )
                }
            ),
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-general',),
                    'fields': tab_general_fields,
                }
            ),
            (
                _('Datasets'),
                {
                    'classes': ('suit-tab', 'suit-tab-datasets',),
                    'fields': (
                        'datasets',
                    )
                }
            ),
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-tags',),
                    'fields': ('tags_pl', 'tags_en'),
                }
            )
        ]
        return fieldsets + self.get_translations_fieldsets()

    def application_logo(self, obj):
        return obj.application_logo or '-'
    application_logo.short_description = _('Logo')

    def illustrative_graphics_img(self, obj):
        return obj.illustrative_graphics_img or '-'
    illustrative_graphics_img.short_description = _('Illustrative graphics')

    def preview_link(self, obj):
        return mark_safe('<a href="%s" class="btn" target="_blank">%s</a>' % (obj.frontend_preview_url, _('Preview')))
    preview_link.allow_tags = True
    preview_link.short_description = _('Preview link')

    def save_model(self, request, obj, form, change):
        if 'slug' in form.cleaned_data:
            if form.cleaned_data['slug'] == "":
                obj.slug = slugify(form.cleaned_data['title'])
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        if 'external_datasets' in form.cleaned_data:
            obj.external_datasets = form.cleaned_data['external_datasets']
        super().save_model(request, obj, form, change)


@admin.register(ApplicationTrash)
class TrashApplicationAdmin(HistoryMixin, TrashMixin):
    list_display = ['title', 'author', 'url']
    search_fields = ['title', 'author', 'url']

    readonly_fields = [
        'title', 'author', 'datasets', 'image', 'notes', 'slug', 'status', 'tags_list_pl', 'tags_list_en', 'url',
    ]
    fields = [x for x in readonly_fields] + ['is_removed']

    def tags_list_pl(self, instance):
        return instance.tags_as_str(lang='pl')
    tags_list_pl.short_description = _('Tags') + ' (PL)'

    def tags_list_en(self, instance):
        return instance.tags_as_str(lang='en')
    tags_list_en.short_description = _('Tags') + ' (EN)'


class ApplicationProposalMixin(ActionsMixin, CRUDMessageMixin, HistoryMixin,
                               DecisionStatusLabelAdminMixin, MCODAdminMixin):
    delete_selected_msg = _('Delete selected application proposals')
    is_history_other = True
    is_history_with_unknown_user_rows = True
    obj_gender = 'f'
    ordering = ('-report_date', )
    search_fields = ['title']

    def application_logo(self, obj):
        return obj.application_logo or '-'
    application_logo.short_description = _('Logo')
    application_logo.admin_order_field = 'image'

    def illustrative_graphics_img(self, obj):
        return obj.illustrative_graphics_img or '-'
    illustrative_graphics_img.short_description = _('Illustrative graphics')
    illustrative_graphics_img.admin_order_field = 'illustrative_graphics'

    def datasets_admin(self, obj):
        return obj.datasets_admin or '-'
    datasets_admin.short_description = _('Datasets being used to build application')

    def external_datasets_admin(self, obj):
        return obj.external_datasets_admin or '-'
    external_datasets_admin.short_description = _('External public data used')
    external_datasets_admin.admin_order_field = 'external_datasets'

    def get_list_display(self, request):
        if request.method == 'GET' and request.GET.get('decision') == 'taken':
            return ['title', 'author', 'application_logo', 'report_date', 'decision', 'decision_date']
        return ['title', 'author', 'application_logo', 'report_date', 'decision']

    def has_add_permission(self, request, obj=None):
        return False


class ApplicationProposalAdmin(ApplicationProposalMixin, ExportCsvMixin, SoftDeleteMixin, admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general'),
                'fields': (
                    'title',
                    'url',
                    'notes',
                    'applicant_email',
                    'author',
                    'application_logo',
                    'illustrative_graphics_img',
                    'datasets_admin',
                    'external_datasets_admin',
                    'keywords',
                    'comment',
                    'report_date',
                    ('decision', 'decision_date'),
                )
            }
        ),
    ]
    form = ApplicationProposalForm
    list_filter = [
        DecisionFilter,
    ]
    readonly_fields = [
        'title',
        'url',
        'notes',
        'applicant_email',
        'author',
        'application_logo',
        'illustrative_graphics_img',
        'datasets_admin',
        'external_datasets_admin',
        'keywords',
        'report_date',
        'decision_date',
    ]
    suit_form_tabs = (
        ('general', _('General')),
    )

    @property
    def admin_url(self):
        return super().admin_url + '?decision=not_taken'

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        create_app = obj.tracker.has_changed('decision') and obj.is_accepted and not obj.application
        super().save_model(request, obj, form, change)
        if create_app:
            create_application_task.s(obj.id).apply_async(countdown=1)
            self.message_user(request, _('Application creation task was launched!'), level=messages.SUCCESS)


class ApplicationProposalTrashAdmin(ApplicationProposalMixin, TrashMixin):
    readonly_fields = [
        'title',
        'url',
        'notes',
        'applicant_email',
        'author',
        'application_logo',
        'illustrative_graphics_img',
        'datasets_admin',
        'external_datasets_admin',
        'keywords',
        'comment',
        'report_date',
        'decision',
        'decision_date',
    ]
    fields = [x for x in readonly_fields] + ['is_removed']


admin.site.register(ApplicationProposal, ApplicationProposalAdmin)
admin.site.register(ApplicationProposalTrash, ApplicationProposalTrashAdmin)
