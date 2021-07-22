from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from mcod.lib.admin_mixins import (
    ActionsMixin,
    CRUDMessageMixin,
    DecisionFilter,
    HistoryMixin,
    SoftDeleteMixin,
    TrashMixin,
    LangFieldsOnlyMixin,
    StatusLabelAdminMixin,
    DecisionStatusLabelAdminMixin,
    DynamicAdminListDisplayMixin,
    MCODAdminMixin
)
from mcod.reports.admin import ExportCsvMixin
from mcod.suggestions.forms import (
    AcceptedDatasetSubmissionForm,
    DatasetCommentForm,
    DatasetSubmissionForm,
    ResourceCommentForm,
)
from mcod.suggestions.models import (
    AcceptedDatasetSubmission,
    AcceptedDatasetSubmissionTrash,
    DatasetComment,
    DatasetCommentTrash,
    DatasetSubmission,
    DatasetSubmissionTrash,
    ResourceComment,
    ResourceCommentTrash,
)
from mcod.suggestions.tasks import create_accepted_dataset_suggestion_task


class CommentAdminMixin(DynamicAdminListDisplayMixin, DecisionStatusLabelAdminMixin, ActionsMixin, CRUDMessageMixin,
                        HistoryMixin, ExportCsvMixin, SoftDeleteMixin, MCODAdminMixin, admin.ModelAdmin):
    is_history_other = True
    is_history_with_unknown_user_rows = True
    list_filter = [
        DecisionFilter,
    ]
    obj_gender = 'f'
    suit_form_tabs = (
        ('general', _('General')),
    )

    def _comment(self, obj):
        return obj.comment or '-'
    _comment.short_description = _('text of comment')

    def _data_provider_url(self, obj):
        return obj.data_provider_url or '-'
    _data_provider_url.short_description = _('Data provider')

    def _decision(self, obj):
        return obj.get_decision_display() or _('Decision not taken')
    _decision.short_description = _('decision')
    _decision.admin_order_field = 'decision'

    def _editor_email(self, obj):
        return obj.editor_email or '-'
    _editor_email.short_description = _('editor e-mail')

    def _truncated_comment(self, obj):
        return obj.truncated_comment or '-'
    _truncated_comment.short_description = _('notes')
    _truncated_comment.admin_order_field = 'comment'

    def changelist_view(self, request, extra_context=None):
        query_string = request.META.get('QUERY_STRING', '')
        if 'decision' not in query_string:
            return HttpResponseRedirect(request.path + '?decision=not_taken')
        return super().changelist_view(request, extra_context=extra_context)

    def get_list_display(self, request):
        if request.method == 'GET' and request.GET.get('decision') == 'taken':
            return self.replace_attributes(['_title', '_truncated_comment', 'report_date', '_decision', 'decision_date'])
        return self.replace_attributes(['_title', '_truncated_comment', 'report_date', '_decision'])

    def has_add_permission(self, request, obj=None):
        return False


class DatasetCommentAdmin(CommentAdminMixin):
    fieldsets = [
        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general'),
                'fields': (
                    '_title',
                    '_comment',
                    '_editor_email',
                    '_data_url',
                    '_data_provider_url',
                    'editor_comment',
                    'report_date',
                    'is_data_provider_error',
                    'is_user_error',
                    'is_portal_error',
                    'is_other_error',
                    'decision',
                    'decision_date',
                )
            }
        ),
    ]
    form = DatasetCommentForm
    list_select_related = ('dataset',)
    readonly_fields = [
        'decision_date',
        'report_date',
        '_comment',
        '_data_url',
        '_data_provider_url',
        '_editor_email',
        '_title',
    ]
    search_fields = ['dataset__title', 'comment']

    def _data_url(self, obj):
        return obj.data_url or '-'
    _data_url.short_description = _('comment reported for dataset')

    def _title(self, obj):
        return obj.dataset.title or '-'
    _title.short_description = _('Title')
    _title.admin_order_field = 'dataset__title'

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('datasets.delete_dataset')


class CommentAdminTrashMixin(TrashMixin):
    fieldsets = None
    is_history_other = True
    is_history_with_unknown_user_rows = True
    suit_form_tabs = None
    readonly_fields = [
        '_title',
        '_comment',
        '_editor_email',
        '_data_url',
        '_data_provider_url',
        'editor_comment',
        'report_date',
        'decision',
        'decision_date',
    ]
    fields = [x for x in readonly_fields] + ['is_removed']

    def delete_model(self, request, obj):
        obj.delete(soft=False)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete(soft=False)


class DatasetSubmissionAdminMixin(CRUDMessageMixin, SoftDeleteMixin, HistoryMixin,
                                  MCODAdminMixin, admin.ModelAdmin):
    is_history_other = True
    is_history_with_unknown_user_rows = True
    obj_gender = 'f'
    search_fields = ['title']
    suit_form_tabs = (
        ('general', _('General')),
    )

    def has_add_permission(self, request):
        return False


class DatasetSubmissionAdmin(DynamicAdminListDisplayMixin, DecisionStatusLabelAdminMixin,
                             ExportCsvMixin, DatasetSubmissionAdminMixin):
    form = DatasetSubmissionForm
    list_filter = [
        DecisionFilter,
    ]
    fields = (
        'title',
        'notes',
        'organization_name',
        'data_link',
        'potential_possibilities',
        'comment',
        'submission_date',
        ('decision', 'decision_date'),
    )
    readonly_fields = (
        'title',
        'notes',
        'organization_name',
        'data_link',
        'potential_possibilities',
        'submission_date',
        'decision_date',
    )

    def _decision(self, obj):
        return obj.get_decision_display() or _('Decision not taken')
    _decision.short_description = _('decision')
    _decision.admin_order_field = 'decision'

    def _notes(self, obj):
        return obj.truncated_notes or '-'
    _notes.short_description = _('Data description')
    _notes.admin_order_field = 'notes'

    def changelist_view(self, request, extra_context=None):
        query_string = request.META.get('QUERY_STRING', '')
        if 'decision' not in query_string:
            return HttpResponseRedirect(request.path + '?decision=not_taken')
        return super(DatasetSubmissionAdmin, self).changelist_view(request, extra_context=extra_context)

    def get_list_display(self, request):
        if request.method == 'GET' and request.GET.get('decision') == 'taken':
            return self.replace_attributes(['title', '_notes', 'submission_date', '_decision', 'decision_date'])
        return self.replace_attributes(['title', '_notes', 'submission_date', '_decision'])

    def save_model(self, request, obj, form, change):
        obj.modified_by = request.user
        create_needed = obj.tracker.has_changed('decision') and obj.is_accepted and not obj.accepted_dataset_submission
        super().save_model(request, obj, form, change)
        if create_needed:
            create_accepted_dataset_suggestion_task.s(obj.id).apply_async(countdown=1)
            self.message_user(
                request, _('Create accepted dataset suggestion task was launched!'), level=messages.SUCCESS)


class AcceptedDatasetSubmissionAdmin(DynamicAdminListDisplayMixin, LangFieldsOnlyMixin,
                                     StatusLabelAdminMixin, DatasetSubmissionAdminMixin):
    fields = (
        'title',
        'notes',
        'organization_name',
        'data_link',
        'potential_possibilities',
        'comment',
        'decision_date',
        'status',
        'is_active',
    )
    form = AcceptedDatasetSubmissionForm
    list_display = [
        '_title',
        '_notes',
        'submission_date',
        'decision_date',
        'status',
    ]
    readonly_fields = ['comment', 'decision_date']

    def __init__(self, model, admin_site):
        super(AcceptedDatasetSubmissionAdmin, self).__init__(model, admin_site)
        self.suit_form_tabs = (
            ('general', _('General')),
            *LangFieldsOnlyMixin.get_translations_tabs()
        )

    def _title(self, obj):
        return obj.title
    _title.short_description = _('Title')
    _title.admin_order_field = 'title'

    def _notes(self, obj):
        return obj.truncated_notes or '-'
    _notes.short_description = _('Notes')
    _notes.admin_order_field = 'notes'

    def get_fields(self, request, obj=None):
        """
        Hook for specifying fields.
        """
        if self.fields:
            fields_list = list(self.fields)
            fields = tuple(fields_list[:8] + ['is_published_for_all'] + fields_list[8:])
            return fields
        # _get_form_for_get_fields() is implemented in subclasses.
        form = self._get_form_for_get_fields(request, obj)
        return [*form.base_fields, *self.get_readonly_fields(request, obj)]

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(AcceptedDatasetSubmissionAdmin, self).get_fieldsets(request, obj)
        fieldsets = [
            (
                None,
                {
                    'classes': ('suit-tab', 'suit-tab-general',),
                    'fields': fieldsets[0][1]['fields']
                }
            )]
        translated_fields = self.get_translations_fieldsets()
        translated_fields[0][1]['fields'].remove('slug_en')
        fieldsets += translated_fields
        return fieldsets


class DatasetSubmissionTrashAdmin(TrashMixin, DatasetSubmissionAdmin):
    readonly_fields = [
        'title',
        'notes',
        'organization_name',
        'data_link',
        'potential_possibilities',
        'comment',
        'submission_date',
        'decision',
        'decision_date',
    ]
    fields = [x for x in readonly_fields] + ['is_removed']

    def delete_model(self, request, obj):
        obj.delete(soft=False)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete(soft=False)


class AcceptedDatasetSubmissionTrashAdmin(TrashMixin, AcceptedDatasetSubmissionAdmin):
    readonly_fields = AcceptedDatasetSubmissionAdmin.fields
    fields = [x for x in readonly_fields] + ['is_removed']

    def delete_model(self, request, obj):
        obj.delete(soft=False)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete(soft=False)


class ResourceCommentAdmin(CommentAdminMixin):
    fieldsets = [
        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general'),
                'fields': (
                    '_title',
                    '_comment',
                    '_editor_email',
                    '_data_url',
                    '_data_provider_url',
                    'editor_comment',
                    'report_date',
                    'is_data_provider_error',
                    'is_user_error',
                    'is_portal_error',
                    'is_other_error',
                    'decision',
                    'decision_date',
                )
            }
        ),
    ]
    form = ResourceCommentForm
    list_select_related = ('resource', )
    readonly_fields = [
        'decision_date',
        'report_date',
        '_comment',
        '_data_url',
        '_data_provider_url',
        '_editor_email',
        '_title',
    ]
    search_fields = ['resource__title', 'comment']

    def _data_url(self, obj):
        return obj.data_url or '-'
    _data_url.short_description = _('comment reported for data')

    def _title(self, obj):
        return obj.resource.title or '-'
    _title.short_description = _('Title')
    _title.admin_order_field = 'resource__title'

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('resources.delete_resource')


class DatasetCommentTrashAdmin(CommentAdminTrashMixin, DatasetCommentAdmin):
    pass


class ResourceCommentTrashAdmin(CommentAdminTrashMixin, ResourceCommentAdmin):
    pass


admin.site.register(DatasetSubmission, DatasetSubmissionAdmin)
admin.site.register(DatasetSubmissionTrash, DatasetSubmissionTrashAdmin)
admin.site.register(AcceptedDatasetSubmission, AcceptedDatasetSubmissionAdmin)
admin.site.register(AcceptedDatasetSubmissionTrash, AcceptedDatasetSubmissionTrashAdmin)

admin.site.register(DatasetComment, DatasetCommentAdmin)
admin.site.register(DatasetCommentTrash, DatasetCommentTrashAdmin)
admin.site.register(ResourceComment, ResourceCommentAdmin)
admin.site.register(ResourceCommentTrash, ResourceCommentTrashAdmin)
