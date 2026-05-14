from typing import Any, Mapping
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect


def axes_lockout(
    request: HttpRequest,
    credentials: Mapping[str, Any],
    *args: Any,
    **kwargs: Any,
) -> HttpResponseRedirect:
    """
    login.html doesn't use messages, so we are passing lockout message
    to session. Opposite to CMS, where messages are used.
    """
    base_url = request.path
    next_value = request.POST.get("next") or request.GET.get("next")

    if next_value:
        url = f"{base_url}?next={quote(next_value, safe='/')}"
    else:
        url = base_url

    if settings.COMPONENT == settings.COMPONENT_ADMIN:
        request.session["axes_lockout_message"] = settings.AXES_FAIL_MESSAGE

    if settings.COMPONENT == settings.COMPONENT_CMS:
        messages.error(request, settings.AXES_FAIL_MESSAGE)

    return redirect(url)
