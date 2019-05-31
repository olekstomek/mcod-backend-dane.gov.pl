from django.contrib import messages
from django.db import connection
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from mcod.lib.jwt import get_auth_token
from mcod import settings


class PostgresConfMiddleware(object):
    """ Simple middleware that adds the request object in thread local stor    age."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_request(self, request, *args, **kwargs):
        # TODO - nie wpadam tutaj w czasie pracy z adminem
        if request.user.id:
            connection.cursor().execute(
                'SET myapp.userid = "{}"'.format(request.user.id)
            )

    def process_view(self, request, *args, **kwargs):
        if request.user.id:
            connection.cursor().execute(
                'SET myapp.userid = "{}"'.format(request.user.id)
            )


class UserTokenMiddleware(object):
    """
    Middleware to set user mcod_token cookie
    If user is authenticated and there is no cookie, set the cookie,
    If the user is not authenticated and the cookie remains, delete it
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_template_response(self, request, response):
        # if user and no cookie, set cookie

        token_name = settings.SESSION_ENV_PREFIX + "mcod_token"

        domain = request.META.get("HTTP_HOST", "localhost")
        if domain.startswith('admin.'):
            domain = domain.replace('admin.', "")
        elif domain.startswith('localhost'):
            domain = domain.split(":")[0]

        if request.user.is_authenticated and not request.COOKIES.get(token_name):
            token = get_auth_token(request.user.email, request.user.system_role, request.session.session_key)
            response.set_cookie(token_name, token, domain=domain)
        elif not request.user.is_authenticated:
            # else if no user and cookie remove user cookie, logout
            response.delete_cookie(token_name, domain=domain)

        return response


class ComplementUserDataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user and not request.user.is_anonymous:
            if request.user.is_normal_staff and not request.user.has_complete_staff_data:
                user_edit_form_path = reverse("admin:users_user_change", args=(request.user.id,))
                allowed_paths = {
                    user_edit_form_path,
                    reverse('admin:logout'),
                }
                if request.path not in allowed_paths:
                    messages.add_message(request, messages.ERROR,
                                         _('Your account data is incomplete. Full name and phone number must be given'))
                    return redirect(user_edit_form_path)
        return self.get_response(request)
