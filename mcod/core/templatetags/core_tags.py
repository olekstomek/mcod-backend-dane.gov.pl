from django import template
from django.apps import apps
from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from suit.templatetags.suit_list import result_list_with_context
from django.utils.html import format_html
from suit.templatetags.suit_menu import get_admin_site, Menu as SuitMenu

from mcod.core.db.models import TrashModelBase
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

    def init_config(self):
        super().init_config()
        if not is_enabled('S15_guides.be'):
            self.conf_menu = [x for x in self.conf_menu if '/guides/guide' not in x.get('url', '')]


@register.filter()
def to_accusative(value, model):
    verbose_name = str(model._meta.verbose_name)  # declared in Meta
    try:
        new_name = force_text(model.accusative_case())  # a custom class method (lives in your Model)
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
    return instance._meta.get_field(field_name).verbose_name.title()


@register.simple_tag
def is_unleash_enabled(name):
    return is_enabled(name)


@register.inclusion_tag('admin/change_list_results.html', takes_context=True)
def mcod_result_list_with_context(context, cl):
    res = result_list_with_context(context, cl)
    if is_enabled('S21_admin_ui_changes.be'):
        for sub_list in res['results']:
            sub_list[1] = mark_safe(sub_list[1].replace('<th', '<td').replace('/th>', '/td>'))
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

    is_trash = isinstance(model, TrashModelBase)
    has_trash = hasattr(model, 'trash_class') and is_trash is False
    trash_url = None
    if has_trash:
        trash_url = reverse('admin:%s_%s_changelist' % (app_label, model.trash_class._meta.model_name), current_app='admin')

    extra_data = {
        'is_trash': is_trash,
        'trash_url': trash_url,
    }
    return extra_data
