from django import template
from django.conf import settings
from django.http import HttpRequest
from django.utils.encoding import force_text
from django.utils.html import format_html
from suit.templatetags.suit_menu import get_admin_site, Menu as SuitMenu

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
