from django import template
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest
from django.template.defaultfilters import capfirst
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from suit.templatetags.suit_list import result_list_with_context
from django.utils.html import format_html
from suit.templatetags.suit_menu import get_admin_site, Menu as SuitMenu
from suit.templatetags.suit_tags import field_contents_foreign_linked

from mcod.unleash import is_enabled

register = template.Library()


@register.simple_tag(takes_context=True)
def get_admin_menu(context, request):
    if not isinstance(request, HttpRequest):
        return None

    try:
        template_response = get_admin_site(context.current_app).index(request)
    except AttributeError:
        template_response = get_admin_site(context.request.resolver_match.namespace).index(request)

    try:
        app_list = template_response.context_data['app_list']
    except Exception:
        return

    return Menu(context, request, app_list).get_app_list()


class Menu(SuitMenu):

    def get_native_model_url(self, model):
        return model.get('admin_url') or model.get('add_url') or ''

    def activate_models(self, app, match_by_name=False):
        super().activate_models(app, match_by_name=match_by_name)
        if self.request.path in ('/showcases/showcaseproposal/', '/suggestions/datasetsubmission/'):
            # fix inactive links in menu.
            for model in app['models']:
                if (self.request.path == '/showcases/showcaseproposal/' and
                        model.get('name') == 'showcases.showcaseproposal'):
                    model['is_active'] = True

                if (self.request.path == '/suggestions/datasetsubmission/' and
                        model.get('name') == 'suggestions.datasetsubmission'):
                    model['is_active'] = True

                # Mark parent as active too
                if model['is_active'] and not self.app_activated:
                    app['is_active'] = self.app_activated = True


@register.filter()
def to_accusative(value, model):
    verbose_name = str(model._meta.verbose_name)  # declared in Meta
    try:
        new_name = force_str(model.accusative_case())  # a custom class method (lives in your Model)
    except AttributeError:
        return format_html(value)
    if value:
        return format_html(value.replace(verbose_name, new_name))  # button on list_view
    return format_html(new_name)  # change form


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


@register.simple_tag
def get_verbose_field_name(instance, field_name):
    return capfirst(instance._meta.get_field(field_name).verbose_name)


@register.simple_tag
def is_unleash_enabled(name):
    return is_enabled(name)


@register.inclusion_tag('admin/change_list_results.html', takes_context=True)
def mcod_result_list_with_context(context, cl):
    res = result_list_with_context(context, cl)
    for sub_list in res['results']:
        for i, element in enumerate(sub_list):
            sub_list[i] = mark_safe(element.replace('<th', '<td').replace('/th>', '/td>'))
    return res


@register.filter()
def inline_task_status_class(task_status):
    css_classes = {
        'SUCCESS': 'label label-success',
        'PENDING': 'label label-warning',
        'FAILURE': 'label label-important'
    }
    return css_classes.get(task_status, 'label')


@register.filter()
def add_required_span_tag(label_tag):
    split_label = label_tag.split('</label>')
    result_tag = format_html(
        f'{split_label[0]}<span>(pole wymagane)</span></label>') if 'required' in label_tag else label_tag
    return result_tag


@register.simple_tag
def get_model_extra_data(app_label, object_name):
    model = apps.get_model(app_label, object_name)

    is_trash = getattr(model, 'is_trash', False)
    has_trash = hasattr(model, 'trash_class') and is_trash is False
    trash_url = None
    if has_trash:
        trash_model_admin = admin.site._registry.get(model.trash_class)
        default_trash_url = reverse(f'admin:{app_label}_{model.trash_class._meta.model_name}_changelist', current_app='admin')
        trash_url = getattr(trash_model_admin, 'admin_url', default_trash_url)

    model_admin = admin.site._registry.get(model)
    default_admin_url = reverse(f'admin:{app_label}_{model._meta.model_name}_changelist', current_app='admin')
    admin_url = getattr(model_admin, 'admin_url', default_admin_url)

    extra_data = {
        'is_trash': is_trash,
        'trash_url': trash_url,
        'admin_url': admin_url,
    }
    return extra_data


@register.filter()
def mcod_field_contents_foreign_linked(admin_field):
    file_fields = ['main_file', 'jsonld_converted_file', 'csv_converted_file']
    field = field_contents_foreign_linked(admin_field)
    field_display = field
    if admin_field.field['field'] in file_fields:
        f_field = getattr(admin_field.form.instance, admin_field.field['field'], '')
        file_url = getattr(f_field, 'url', '')
        if file_url:
            field_display = mark_safe("<a href='%s'>%s</a>" % (file_url, field))
    return field_display
