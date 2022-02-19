import json
import nested_admin
from urllib.parse import quote as urlquote

from django.contrib import admin, messages
from django.contrib.admin.utils import quote, unquote
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.defaultfilters import truncatewords
from django.template.response import TemplateResponse
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _, gettext, pgettext_lazy
from modeltrans.translator import get_i18n_field
from modeltrans.utils import get_language
from rules.contrib.admin import ObjectPermissionsModelAdmin as BaseObjectPermissionsModelAdmin

from mcod import settings
from mcod.histories.models import History, LogEntry
from mcod.reports.tasks import generate_csv
from mcod.tags.views import TagAutocompleteJsonView
from mcod.unleash import is_enabled


class MCODChangeList(ChangeList):

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        if hasattr(self.model, 'accusative_case'):
            if self.is_popup:
                title = gettext('Select %s')
            elif self.model_admin.has_change_permission(request):
                title = gettext('Select %s to change')
            else:
                title = gettext('Select %s to view')
            self.title = title % self.model.accusative_case()


class MCODTrashChangeList(ChangeList):

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.title = self.model._meta.verbose_name_plural.capitalize()


class TagAutocompleteMixin:
    def autocomplete_view(self, request):
        return TagAutocompleteJsonView.as_view(model_admin=self)(request)


class DecisionFilter(admin.SimpleListFilter):
    parameter_name = 'decision'
    title = _('decision')
    template = 'admin/decision_filter.html'

    def lookups(self, request, model_admin):
        return (
            ('taken', _('Decision taken')),
            ('not_taken', _('Decision not taken')),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'taken':
            return queryset.with_decision()
        elif val == 'not_taken':
            return queryset.without_decision()
        return queryset


class AddChangeMixin(object):

    def has_add_permission(self, request):
        object_id = request.resolver_match.kwargs.get('object_id')
        obj = None
        if object_id:
            try:
                obj = self.model.raw.get(id=object_id)
            except self.model.DoesNotExist:
                pass
            if obj and obj.is_imported:
                return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_imported:
            return False
        return super().has_change_permission(request, obj=obj)


def export_to_csv(self, request, queryset):
    generate_csv.s(tuple(obj.id for obj in queryset),
                   self.model._meta.label,
                   request.user.id,
                   now().strftime('%Y%m%d%H%M%S.%s')
                   ).apply_async(countdown=1)
    messages.add_message(request, messages.SUCCESS, _('Task for CSV generation queued'))


export_to_csv.short_description = _("Export selected to CSV")


class ExportCsvMixin:

    export_to_csv = False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if self.export_to_csv and request.user.is_superuser:
            actions.update({
                'export_to_csv': (export_to_csv, 'export_to_csv', _("Export selected to CSV"))
            })
        return actions


class SoftDeleteMixin:
    """
    Overrides default queryset.delete() call from base class.
    """

    soft_delete = False

    def delete_queryset(self, request, queryset):
        if self.soft_delete:
            for instance in queryset:
                instance.delete(soft=True)
        else:
            super().delete_queryset(request, queryset)


class CRUDMessageMixin:
    """
    Overrides default messages displayed for user after successful saving of instance.
    """
    obj_gender = None  # options: f=feminine, n=neuter.

    add_msg_template = _('The {name} "{obj}" was added successfully.')
    add_msg_template_f = pgettext_lazy('The {name} "{obj}" was added successfully.', 'feminine')
    add_msg_template_n = pgettext_lazy('The {name} "{obj}" was added successfully.', 'neuter')

    add_continue_msg_template = _('The {name} "{obj}" was added successfully.')
    add_continue_msg_template_f = pgettext_lazy('The {name} "{obj}" was added successfully.', 'feminine')
    add_continue_msg_template_n = pgettext_lazy('The {name} "{obj}" was added successfully.', 'neuter')

    add_addanother_msg_template = _('The {name} "{obj}" was added successfully. You may add another {name} below.')
    add_addanother_msg_template_f = pgettext_lazy(
        'The {name} "{obj}" was added successfully. You may add another {name} below.', 'feminine')
    add_addanother_msg_template_n = pgettext_lazy(
        'The {name} "{obj}" was added successfully. You may add another {name} below.', 'neuter')

    change_msg_template = _('The {name} "{obj}" was changed successfully.')
    change_msg_template_f = pgettext_lazy('The {name} "{obj}" was changed successfully.', 'feminine')
    change_msg_template_n = pgettext_lazy('The {name} "{obj}" was changed successfully.', 'neuter')

    change_continue_msg_template = _('The {name} "{obj}" was changed successfully. You may edit it again below.')
    change_continue_msg_template_f = pgettext_lazy(
        'The {name} "{obj}" was changed successfully. You may edit it again below.', 'feminine')
    change_continue_msg_template_n = pgettext_lazy(
        'The {name} "{obj}" was changed successfully. You may edit it again below.', 'neuter')

    change_saveasnew_msg_template = _('The {name} "{obj}" was added successfully. You may edit it again below.')
    change_saveasnew_msg_template_f = pgettext_lazy(
        'The {name} "{obj}" was added successfully. You may edit it again below.', 'feminine')
    change_saveasnew_msg_template_n = pgettext_lazy(
        'The {name} "{obj}" was added successfully. You may edit it again below.', 'neuter')

    change_addanother_msg_template = _(
        'The {name} "{obj}" was changed successfully. You may add another {name} below.')
    change_addanother_msg_template_f = pgettext_lazy(
        'The {name} "{obj}" was changed successfully. You may add another {name} below.', 'feminine')
    change_addanother_msg_template_n = pgettext_lazy(
        'The {name} "{obj}" was changed successfully. You may add another {name} below.', 'neuter')

    delete_msg_template = _('The %(name)s "%(obj)s" was deleted successfully.')
    delete_msg_template_f = pgettext_lazy('The %(name)s "%(obj)s" was deleted successfully.', 'feminine')
    delete_msg_template_n = pgettext_lazy('The %(name)s "%(obj)s" was deleted successfully.', 'neuter')

    s43_admin_trash_fixes = is_enabled('S43_admin_trash_fixes.be')

    def get_msg_template(self, template_name):
        if self.obj_gender in ['f', 'n']:
            template_name = f'{template_name}_{self.obj_gender}'
        return getattr(self, template_name)

    def response_add(self, request, obj, post_url_continue=None):
        if "_popup" in request.POST:
            return super().response_add(request, obj, post_url_continue=post_url_continue)

        opts = obj._meta
        preserved_filters = self.get_preserved_filters(request)
        obj_url = reverse(
            'admin:%s_%s_change' % (opts.app_label, opts.model_name),
            args=(quote(obj.pk),),
            current_app=self.admin_site.name,
        )
        # Add a link to the object's change form if the user can edit the obj.
        if self.has_change_permission(request, obj):
            obj_repr = format_html('<a href="{}">{}</a>', urlquote(obj_url), obj)
        else:
            obj_repr = str(obj)
        msg_dict = {
            'name': opts.verbose_name.capitalize(),
            'obj': obj_repr,
        }
        if "_continue" in request.POST or (
                # Redirecting after "Save as new".
                "_saveasnew" in request.POST and self.save_as_continue and
                self.has_change_permission(request, obj)):

            msg = self.get_msg_template('add_continue_msg_template')
            if self.has_change_permission(request, obj):
                msg += ' ' + gettext('You may edit it again below.')
            self.message_user(request, format_html(msg, **msg_dict), messages.SUCCESS)
            if post_url_continue is None:
                post_url_continue = obj_url
            post_url_continue = add_preserved_filters(
                {'preserved_filters': preserved_filters, 'opts': opts},
                post_url_continue
            )
            return HttpResponseRedirect(post_url_continue)

        elif "_addanother" in request.POST:
            msg = format_html(self.get_msg_template('add_addanother_msg_template'), **msg_dict)
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)
        else:
            msg = format_html(
                self.get_msg_template('add_msg_template'), **msg_dict)
            self.message_user(request, msg, messages.SUCCESS)
            return self.response_post_save_add(request, obj)

    def _get_obj_url(self, request, obj):
        if self.s43_admin_trash_fixes:
            obj_url = obj.admin_change_url
            if self.model._meta.proxy and not obj.is_removed:
                opts = self.model._meta.concrete_model._meta
                obj_url = reverse(
                    'admin:%s_%s_change' % (opts.app_label, opts.model_name), args=(obj.pk,),
                    current_app=self.admin_site.name)
        else:
            obj_url = urlquote(request.path)
        return obj_url

    def response_change(self, request, obj):
        if "_popup" in request.POST:
            return super().response_change(request, obj)

        opts = self.model._meta
        preserved_filters = self.get_preserved_filters(request)

        obj_url = self._get_obj_url(request, obj)
        msg_dict = {
            'name': opts.verbose_name.capitalize(),
            'obj': format_html('<a href="{}">{}</a>', obj_url, truncatewords(obj, 18)),
        }
        if "_continue" in request.POST:
            msg = format_html(self.get_msg_template('change_continue_msg_template'), **msg_dict)
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        elif "_saveasnew" in request.POST:
            msg = format_html(self.get_msg_template('change_saveasnew_msg_template'), **msg_dict)
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = reverse('admin:%s_%s_change' %
                                   (opts.app_label, opts.model_name),
                                   args=(obj.pk,),
                                   current_app=self.admin_site.name)
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        elif "_addanother" in request.POST:
            msg = format_html(self.get_msg_template('change_addanother_msg_template'), **msg_dict)
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = reverse('admin:%s_%s_add' %
                                   (opts.app_label, opts.model_name),
                                   current_app=self.admin_site.name)
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        else:
            msg = format_html(self.get_msg_template('change_msg_template'), **msg_dict)
            self.message_user(request, msg, messages.SUCCESS)
            return self.response_post_save_change(request, obj)

    def response_delete(self, request, obj_display, obj_id):
        opts = self.model._meta

        if "_popup" in request.POST:
            popup_response_data = json.dumps({
                'action': 'delete',
                'value': str(obj_id),
            })
            return TemplateResponse(request, self.popup_response_template or [
                'admin/%s/%s/popup_response.html' % (opts.app_label, opts.model_name),
                'admin/%s/popup_response.html' % opts.app_label,
                'admin/popup_response.html',
            ], {
                'popup_response_data': popup_response_data,
            })

        self.message_user(
            request,
            self.get_msg_template('delete_msg_template') % {
                'name': opts.verbose_name.capitalize(),
                'obj': truncatewords(obj_display, 18),
            },
            messages.SUCCESS,
        )

        if self.has_change_permission(request, None):
            post_url = reverse(
                'admin:%s_%s_changelist' % (opts.app_label, opts.model_name),
                current_app=self.admin_site.name,
            )
            preserved_filters = self.get_preserved_filters(request)
            post_url = add_preserved_filters(
                {'preserved_filters': preserved_filters, 'opts': opts}, post_url
            )
        else:
            post_url = reverse('admin:index', current_app=self.admin_site.name)
        return HttpResponseRedirect(post_url)


class ModelAdmin(ExportCsvMixin, SoftDeleteMixin, CRUDMessageMixin, admin.ModelAdmin):

    delete_selected_msg = None

    def get_actions(self, request):
        """Override delete_selected action description."""
        actions = super().get_actions(request)
        if self.delete_selected_msg and 'delete_selected' in actions:
            func, action, description = actions.get('delete_selected')
            actions['delete_selected'] = func, action, self.delete_selected_msg
        return actions


class UserAdmin(ExportCsvMixin, SoftDeleteMixin, BaseUserAdmin):
    soft_delete = True


class NestedModelAdmin(SoftDeleteMixin, nested_admin.NestedModelAdmin):
    pass


class ObjectPermissionsModelAdmin(ExportCsvMixin, BaseObjectPermissionsModelAdmin):
    pass


class TrashMixin(ModelAdmin):
    delete_selected_msg = _("Delete selected objects")
    related_objects_query = None
    cant_restore_msg = _('Couldn\'t restore following objects,'
                         ' because their related objects are still removed: {}')

    excluded_actions = ['export_to_csv']

    actions = ['restore_objects']

    def get_actions(self, request):
        actions = super().get_actions(request)
        for action in self.excluded_actions:
            actions.pop(action, None)
        return actions

    def restore_objects(self, request, queryset):
        to_restore = queryset
        cant_restore = None
        if self.related_objects_query:
            query = {self.related_objects_query + '__is_removed': True}
            to_restore = to_restore.exclude(**query)
            cant_restore = queryset.filter(**query)
        for obj in to_restore:
            obj.is_removed = False
            obj.save()
        if cant_restore is not None:
            self.message_user(request, self.cant_restore_msg.format(', '.join([str(obj) for obj in cant_restore])))
        self.message_user(request, _('Successfully restored objects: {}').format(to_restore.count()))

    restore_objects.short_description = _('Restore selected objects')

    def get_changelist(self, request, **kwargs):
        return MCODTrashChangeList

    def get_queryset(self, request):
        return self.model.trash.all()

    def has_add_permission(self, request, obj=None):
        return False

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if self.s43_admin_trash_fixes:
            context['show_save_and_continue'] = False
        if hasattr(self.model, 'accusative_case'):
            if add:
                title = _('Add %s - trash')
            elif self.has_change_permission(request, obj):
                title = _('Change %s - trash')
            else:
                title = _('View %s - trash')
            context['title'] = title % self.model.accusative_case()
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'is_removed':
            kwargs['label'] = _('Removed:')
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class HistoryMixin(object):

    is_history_other = False
    is_history_with_unknown_user_rows = False

    def get_history(self, obj):
        queryset = LogEntry.objects.get_for_object(obj)
        if not self.is_history_with_unknown_user_rows:
            queryset = queryset.exclude(actor_id=1)
        return queryset

    def get_history_action_list(self, table_name, obj):
        if self.is_history_other:
            return History.objects.get_history_other(table_name, obj.id, self.is_history_with_unknown_user_rows)
        qs = History.objects.filter(table_name=table_name, row_id=obj.id)
        if not self.is_history_with_unknown_user_rows:
            qs = qs.exclude(change_user_id=1)
        return qs.order_by('-change_timestamp')

    def has_history_permission(self, request, obj):
        return self.has_change_permission(request, obj)

    def history_view(self, request, object_id, extra_context=None):
        """The 'history' admin view for this model."""
        # First check if the user can see this history.
        model = self.model
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, model._meta, object_id)

        if not self.has_history_permission(request, obj):
            raise PermissionDenied

        # Then get the history for this object.
        opts = model._meta
        app_label = opts.app_label
        action_list = self.get_history(obj)
        context = dict(
            self.admin_site.each_context(request),
            title=_('Change history: %s') % obj,
            action_list=action_list,
            module_name=str(capfirst(opts.verbose_name_plural)),
            object=obj,
            opts=opts,
            preserved_filters=self.get_preserved_filters(request),
        )
        context.update(extra_context or {})

        request.current_app = self.admin_site.name

        return TemplateResponse(request, self.object_history_template or [
            "admin/%s/%s/object_history.html" % (app_label, opts.model_name),
            "admin/%s/object_history.html" % app_label,
            "admin/object_history.html"
        ], context)

    def obj_history(self, obj):
        try:
            product_url = reverse(
                "admin:%s_%s_history" % (obj._meta.app_label, obj._meta.model_name),
                args=(obj.id,)
            )
        except NoReverseMatch:
            product_url = ''

        html = mark_safe('<a href="%s" target="_blank">%s</a>' % (
            product_url,
            _("History")
        ))

        return html

    obj_history.short_description = _('History')


class LangFieldsOnlyMixin(object):
    def get_form(self, request, obj=None, **kwargs):
        i18n_field = get_i18n_field(self.model)
        language = get_language()

        for field in i18n_field.get_translated_fields():
            if field.language == language:
                field.blank = field.original_field.blank

        return super().get_form(request, obj=obj, **kwargs)

    def get_translations_fieldsets(self):
        i18n_field = get_i18n_field(self.model)
        fieldsets = []
        for lang_code in settings.MODELTRANS_AVAILABLE_LANGUAGES:
            if lang_code == settings.LANGUAGE_CODE:
                continue
            tab_name = 'general' if lang_code == settings.LANGUAGE_CODE else f'lang-{lang_code}'
            fieldset = (None, {
                'classes': ('suit-tab', f'suit-tab-{tab_name}',),
                'fields': [
                    f'{field.name}' for field in i18n_field.get_translated_fields()
                    if field.name.endswith(lang_code)
                ]
            })
            fieldsets.append(fieldset)
        return fieldsets

    @staticmethod
    def get_translations_tabs():
        return tuple((f'lang-{lang_code}', _(f'Translation ({lang_code.upper()})'))
                     for lang_code in settings.MODELTRANS_AVAILABLE_LANGUAGES
                     if lang_code is not settings.LANGUAGE_CODE)


class AdminListMixin(object):

    class Media:
        css = {
            'all': ('./fontawesome/css/all.min.css',)
        }

    task_status_to_css_class = {
        'SUCCESS': 'fas fa-check text-success',
        'PENDING': 'fas fa-question-circle text-warning',
        'FAILURE': 'fas fa-times-circle text-error',
        None: 'fas fa-minus-circle text-light',
        '': 'fas fa-minus-circle text-light',
    }

    task_status_tooltip = {
        'SUCCESS': _('Correct Validation'),
        'PENDING': _('Validation in progress'),
        'FAILURE': _('Validation failed'),
        None: _('No validation'),
        '': _('No validation'),
    }

    def _format_list_status(self, val):
        return format_html(f'<i class="{self.task_status_to_css_class[val]}"'
                           f' title="{self.task_status_tooltip[val]}"></i>')


class DynamicAdminListDisplayMixin:

    def replace_attributes(self, source_list):
        for mixin_label_attr in self.mixins_label_attribute.values():
            source_list = [
                display_attr if display_attr != mixin_label_attr and display_attr != f'_{mixin_label_attr}'
                else f'{mixin_label_attr}_label' for display_attr in source_list]
        return source_list

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        return self.replace_attributes(list_display)


class RelatedUserDisplayFormatBase:

    @staticmethod
    def _format_user_display(val, default='Brak'):
        user, host = val.split('@') if val and '@' in val else (None, None)
        if user and host:
            return format_html(f'<span class="email-label-user" title="{val}">{user}</span>'
                               f'<span class="email-label-host">{host}</span>')
        return default


class CreatedByDisplayAdminMixin(RelatedUserDisplayFormatBase):

    def __init_subclass__(cls, **kwargs):
        mixin_dict = {'CreatedByDisplayAdminMixin': 'created_by'}
        if not hasattr(cls, 'mixins_label_attribute'):
            cls.mixins_label_attribute = mixin_dict
        else:
            cls.mixins_label_attribute.update(mixin_dict)
        super().__init_subclass__(**kwargs)

    def created_by_label(self, obj):
        return self._format_user_display(obj.created_by.email if obj.created_by else '')

    created_by_label.admin_order_field = 'created_by'
    created_by_label.short_description = _('Created by')


class ModifiedByDisplayAdminMixin(RelatedUserDisplayFormatBase):

    def __init_subclass__(cls, **kwargs):
        mixin_dict = {'ModifiedByDisplayAdminMixin': 'modified_by'}
        if not hasattr(cls, 'mixins_label_attribute'):
            cls.mixins_label_attribute = mixin_dict
        else:
            cls.mixins_label_attribute.update(mixin_dict)
        super().__init_subclass__(**kwargs)

    def modified_by_label(self, obj):
        return self._format_user_display(obj.created_by.email if obj.created_by else '')

    modified_by_label.admin_order_field = 'modified_by'
    modified_by_label.short_description = _('Modified by')


class OrderedByDisplayAdminMixin(RelatedUserDisplayFormatBase):

    def __init_subclass__(cls, **kwargs):
        mixin_dict = {'OrderedByDisplayAdminMixin': 'ordered_by'}
        if not hasattr(cls, 'mixins_label_attribute'):
            cls.mixins_label_attribute = mixin_dict
        else:
            cls.mixins_label_attribute.update(mixin_dict)
        super().__init_subclass__(**kwargs)

    def ordered_by_label(self, obj):
        return self._format_user_display(obj.ordered_by.email if obj.ordered_by else '@')

    ordered_by_label.admin_order_field = 'ordered_by'
    ordered_by_label.short_description = _('Ordered by')


class FormatLabelBaseMixin:
    STATUS_CSS_CLASSES = {}

    def _format_label(self, obj, mixin_class):
        labeled_attribute = self.mixins_label_attribute[mixin_class]
        self_get_label_fn = getattr(self, f'get_{labeled_attribute}_label')
        self_get_value_fn = getattr(self, f'get_{labeled_attribute}_value')
        return format_html(
            f'<span class="{self.STATUS_CSS_CLASSES.get(self_get_value_fn(obj), "label")}">'
            f'{self_get_label_fn(obj)}</span>')


class BaseStatusLabelAdminMixin(FormatLabelBaseMixin):
    STATUS_CSS_CLASSES = {
        'published': 'label label-success',
        'draft': 'label label-warning'
    }

    def __init_subclass__(cls, **kwargs):
        mixin_dict = {'BaseStatusLabelAdminMixin': 'status'}
        if not hasattr(cls, 'mixins_label_attribute'):
            cls.mixins_label_attribute = mixin_dict
        else:
            cls.mixins_label_attribute.update(mixin_dict)
        super().__init_subclass__(**kwargs)

    def status_label(self, obj):
        return self._format_label(obj, 'BaseStatusLabelAdminMixin')

    status_label.admin_order_field = 'status'
    status_label.short_description = _('status')


class StatusLabelAdminMixin(BaseStatusLabelAdminMixin):

    STATUS_CSS_CLASSES = {
        'published': 'label label-success',
        'draft': 'label label-warning',
        'publication_finished': 'label label-info',
    }

    def get_status_value(self, obj):
        return obj.status

    def get_status_label(self, obj):
        return obj.STATUS[obj.status]


class TaskStatusLabelAdminMixin(BaseStatusLabelAdminMixin):

    STATUS_CSS_CLASSES = {
        'SUCCESS': 'label label-success',
        'PENDING': 'label label-warning',
        'FAILURE': 'label label-important'
    }

    def get_status_value(self, obj):
        if hasattr(obj, 'task'):
            status_value = obj.task.status if obj.task else 'PENDING'
        else:
            status_value = obj.status
        return status_value

    def get_status_label(self, obj):
        if hasattr(obj, 'task'):
            status_label = _(obj.task.status) if obj.task else _('PENDING')
        else:
            status_label = _(obj.status)
        return status_label


class StateStatusLabelAdminMixin(FormatLabelBaseMixin):

    STATUS_CSS_CLASSES = {
        'active': 'label label-success',
        'pending': 'label label-warning',
        'blocked': 'label label-important'
    }

    def __init_subclass__(cls, **kwargs):
        mixin_dict = {'StateStatusLabelAdminMixin': 'state'}
        if not hasattr(cls, 'mixins_label_attribute'):
            cls.mixins_label_attribute = mixin_dict
        else:
            cls.mixins_label_attribute.update(mixin_dict)
        super().__init_subclass__(**kwargs)

    def state_label(self, obj):
        return self._format_label(obj, 'StateStatusLabelAdminMixin')

    def get_state_value(self, obj):
        return obj.state

    def get_state_label(self, obj):
        return obj.get_state_display()

    state_label.admin_order_field = 'state'
    state_label.short_description = _('State')


class DecisionStatusLabelAdminMixin(FormatLabelBaseMixin):
    STATUS_CSS_CLASSES = {
        'accepted': 'label label-success',
        'rejected': 'label label-important',
    }

    def __init_subclass__(cls, **kwargs):
        mixin_dict = {'DecisionStatusLabelAdminMixin': 'decision'}
        if not hasattr(cls, 'mixins_label_attribute'):
            cls.mixins_label_attribute = mixin_dict
        else:
            cls.mixins_label_attribute.update(mixin_dict)
        super().__init_subclass__(**kwargs)

    def decision_label(self, obj):
        return self._format_label(obj, 'DecisionStatusLabelAdminMixin')

    def get_decision_value(self, obj):
        return obj.decision

    def get_decision_label(self, obj):
        return obj.get_decision_display() or _('Decision not taken')

    decision_label.admin_order_field = 'decision'
    decision_label.short_description = _('decision')


class MCODAdminMixin:
    @property
    def admin_url(self):
        opts = self.model._meta
        changelist_url = 'admin:%s_%s_changelist' % (opts.app_label, opts.model_name)
        return reverse(changelist_url)

    def get_changelist(self, request, **kwargs):
        return MCODChangeList

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if hasattr(self.model, 'accusative_case'):
            if add:
                title = _('Add %s')
            elif self.has_change_permission(request, obj):
                title = _('Change %s')
            else:
                title = _('View %s')
            context['title'] = title % self.model.accusative_case()
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)
