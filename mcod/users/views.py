# -*- coding: utf-8 -*-
from smtplib import SMTPException

import falcon
from constance import config
from dal import autocomplete
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password as dj_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail, get_connection
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from mcod.users.serializers import UserCSVSerializer # noqa
from mcod import settings
from mcod.core.api.hooks import login_required
from mcod.core.api.views import BaseView
from mcod.core.versioning import versioned
from mcod.lib.handlers import (
    RetrieveOneHandler,
    CreateHandler,
    UpdateHandler
)
from mcod.lib.jwt import get_auth_token
from mcod.lib.triggers import session_store
from mcod.users.depricated.schemas import (
    Login,
    Registration,
    AccountUpdate,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    ResendActivationEmail
)
from mcod.users.depricated.serializers import (
    LoginSerializer,
    RegistrationSerializer,
    UserSerializer
)
from mcod.users.models import Token

User = get_user_model()


class LoginView(BaseView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST_1_0, *args, **kwargs)

    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    class POST_1_0(CreateHandler):
        database_model = get_user_model()
        deserializer_schema = Login()
        serializer_schema = LoginSerializer(many=False, )  # include_data=('datasets',))

        def _data(self, request, cleaned, *args, **kwargs):
            cleaned['email'] = cleaned['email'].lower()
            try:
                user = User.objects.get(email=cleaned['email'])
            except User.DoesNotExist:
                raise falcon.HTTPUnauthorized(
                    title='401 Unauthorized',
                    description=_('Invalid email or password'),
                    code='account_not_exist'
                )

            if user.state != 'active':
                if user.state not in settings.USER_STATE_LIST or user.state == 'deleted':
                    raise falcon.HTTPUnauthorized(
                        title='401 Unauthorized',
                        description=_('Account is not available'),
                        code='account_unavailable'
                    )

                if user.state in ('draft', 'blocked'):
                    raise falcon.HTTPUnauthorized(
                        title='401 Unauthorized',
                        description=_('Account is blocked'),
                        code='account_unavailable'
                    )

                if user.state == 'pending':
                    raise falcon.HTTPForbidden(
                        title='403 Forbidden',
                        description=_('Email address not confirmed'),
                        code='account_inactive'
                    )

            user = authenticate(request=request, **cleaned)

            if user is None:
                raise falcon.HTTPUnauthorized(
                    title='401 Unauthorized',
                    description=_('Invalid email or password'),
                    code='authorization_error'
                )

            if not hasattr(request, 'session'):
                request.session = session_store()

                request.META = {}
            login(request, user)
            request.session.save()
            user.token = get_auth_token(user.email, user.system_role, request.session.session_key)

            return user


class RegistrationView(BaseView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST_1_0, *args, **kwargs)

    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    class POST_1_0(CreateHandler):
        database_model = get_user_model()
        deserializer_schema = Registration()
        serializer_schema = RegistrationSerializer(many=False, )

        def _clean(self, request, *args, **kwargs):
            cleaned = super()._clean(request, *args, **kwargs)
            if User.objects.filter(email__iexact=cleaned['email']):
                raise falcon.HTTPForbidden(
                    title='403 Forbidden',
                    description=_('This e-mail is already used'),
                    code='emial_already_used'
                )
            cleaned['email'] = cleaned['email'].lower()
            return cleaned

        def _data(self, request, cleaned, *args, **kwargs):
            usr = User.objects.create_user(**cleaned)

            token = usr.email_validation_token
            validation_path = settings.EMAIL_VALIDATION_PATH % token
            link = "%s%s" % (settings.BASE_URL, validation_path)
            # TODO: this is specific for mcod-backend, we should implement more generic solution
            try:
                conn = get_connection(settings.EMAIL_BACKEND)

                msg_plain = render_to_string('mails/confirm-registration.txt',
                                             {'link': link, 'host': settings.BASE_URL})
                msg_html = render_to_string('mails/confirm-registration.html',
                                            {'link': link, 'host': settings.BASE_URL})

                send_mail(
                    'Aktywacja konta',
                    msg_plain,
                    config.ACCOUNTS_EMAIL,
                    [usr.email, ],
                    connection=conn,
                    html_message=msg_html,
                )
            except SMTPException:
                raise falcon.HTTPInternalServerError(
                    description=_('Email cannot be send'),
                    code='email_send_error'
                )

            return usr


class AccountView(BaseView):
    @falcon.before(login_required)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @versioned
    def on_put(self, request, response, *args, **kwargs):
        self.handle(request, response, self.PUT_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_put.version('1.0')
    def on_put(self, request, response, *args, **kwargs):
        self.handle(request, response, self.PUT_1_0, *args, **kwargs)

    class GET_1_0(RetrieveOneHandler):
        database_model = get_user_model()
        serializer_schema = RegistrationSerializer(many=False, )

        def _clean(self, request, *args, **kwargs):
            return request.user

    class PUT_1_0(UpdateHandler):
        database_model = get_user_model()
        deserializer_schema = AccountUpdate()
        serializer_schema = UserSerializer(many=False, )


class LogoutView(BaseView):
    @falcon.before(login_required)
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    class POST_1_0(CreateHandler):
        database_model = get_user_model()

        def _clean(self, request, *args, **kwargs):
            return request.user

        def _data(self, request, cleaned, *args, **kwargs):
            logout(request)

        def _serialize(self, data, meta, links=None, *args, **kwargs):
            return {}


class ResetPasswordView(BaseView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST_1_0, *args, **kwargs)

    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    class POST_1_0(CreateHandler):
        database_model = get_user_model()
        deserializer_schema = PasswordReset()

        def _data(self, request, cleaned, *args, **kwargs):
            try:
                usr = User.objects.get(email=cleaned['email'])
            except User.DoesNotExist:
                raise falcon.HTTPNotFound(
                    description=_('Account not found'),
                    code='account_not_found'
                )

            reset_token = usr.password_reset_token
            reset_path = settings.PASSWORD_RESET_PATH % reset_token
            link = "%s%s" % (settings.BASE_URL, reset_path)
            # TODO: this is specific for mcod-backend, we should implement more generic solution
            try:
                conn = get_connection(settings.EMAIL_BACKEND)

                msg_plain = render_to_string('mails/password-reset.txt', {'link': link, 'host': settings.BASE_URL})
                msg_html = render_to_string('mails/password-reset.html', {'link': link, 'host': settings.BASE_URL})

                send_mail(
                    'Reset hasła',
                    msg_plain,
                    config.ACCOUNTS_EMAIL,
                    [usr.email, ],
                    connection=conn,
                    html_message=msg_html
                )
            except SMTPException:
                raise falcon.HTTPInternalServerError(
                    description=_('Email cannot be send'),
                    code='email_send_error'
                )

            return usr

        def _serialize(self, data, meta, links=None, *args, **kwargs):
            return {'result': 'ok'}


class ConfirmResetPasswordView(BaseView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST_1_0, *args, **kwargs)

    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    class POST_1_0(CreateHandler):
        database_model = get_user_model()
        deserializer_schema = PasswordResetConfirm()

        def _data(self, request, cleaned, token, *args, **kwargs):
            try:
                token = Token.objects.get(token=token, token_type=1)
            except Token.DoesNotExist:
                raise falcon.HTTPNotFound()

            if not token.is_valid:
                raise falcon.HTTPBadRequest(
                    description=_('Expired token'),
                    code='expired_token'
                )

            token.user.set_password(cleaned['new_password1'])
            token.user.save()
            token.invalidate()
            return token.user

        def _serialize(self, data, meta, links=None, *args, **kwargs):
            return {}


class ChangePasswordView(BaseView):
    @falcon.before(login_required)
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    class POST_1_0(CreateHandler):
        database_model = get_user_model()
        deserializer_schema = PasswordChange()
        serializer_schema = UserSerializer(many=False, )

        def _clean(self, request, *args, **kwargs):
            cleaned = super()._clean(request, *args, **kwargs)

            usr = getattr(request, 'user', None)
            is_valid = usr.check_password(cleaned['old_password'])
            if not is_valid:
                raise falcon.HTTPUnprocessableEntity(
                    description=_('Wrong password'),
                )
            try:
                dj_validate_password(cleaned['new_password1'])
            except DjangoValidationError as e:
                raise falcon.HTTPUnprocessableEntity(
                    description=e.error_list[0].message,
                )
            if cleaned['new_password1'] != cleaned['new_password2']:
                raise falcon.HTTPUnprocessableEntity(
                    description=_('Passwords not match'),
                )

            return cleaned

        def _data(self, request, cleaned, *args, **kwargs):
            request.user.set_password(cleaned['new_password1'])
            request.user.save()

        def _serialize(self, data, meta, links=None, *args, **kwargs):
            return {}


class VerifyEmailView(BaseView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(RetrieveOneHandler):
        database_model = get_user_model()

        def _clean(self, request, token, *args, **kwargs):
            try:
                token = Token.objects.get(token=token, token_type=0)
            except Token.DoesNotExist:
                raise falcon.HTTPNotFound()

            if not token.is_valid:
                raise falcon.HTTPBadRequest(
                    description=_('Expired token'),
                    code='expired_token'
                )

            if not token.user.email_confirmed:
                token.user.state = 'active' if token.user.state == 'pending' else token.user.state
                token.user.email_confirmed = timezone.now()
                token.user.save()
                token.invalidate()

        def _data(self, request, cleaned, *args, **kwargs):
            return {}

        def _serialize(self, data, meta, links=None, *args, **kwargs):
            return {}


class ResendActivationEmailView(BaseView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST_1_0, *args, **kwargs)

    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    class POST_1_0(CreateHandler):
        database_model = get_user_model()
        deserializer_schema = ResendActivationEmail()

        def _clean(self, request, *args, **kwargs):
            cleaned = super()._clean(request, *args, **kwargs)
            try:
                usr = User.objects.get(email=cleaned['email'])
            except User.DoesNotExist:
                raise falcon.HTTPNotFound(
                    description=_('Account not found'),
                    code='account_not_found'
                )
            return usr

        def _data(self, request, usr, *args, **kwargs):
            activation_token = usr.email_validation_token
            validation_path = settings.EMAIL_VALIDATION_PATH % activation_token
            link = "%s%s" % (settings.BASE_URL, validation_path)
            try:
                conn = get_connection(settings.EMAIL_BACKEND)
                send_mail(
                    'Reset password',
                    link,
                    config.ACCOUNTS_EMAIL,
                    [usr.email, ], connection=conn
                )
            except SMTPException:
                raise falcon.HTTPInternalServerError(
                    description=_('Email cannot be send'),
                    code='email_send_error'
                )

        def _serialize(self, data, meta, links=None, *args, **kwargs):
            return {}


class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return User.objects.none()

        qs = User.objects.all()

        if self.q:
            qs = qs.filter(email__icontains=self.q)

        return qs


class AdminAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_superuser:
            return User.objects.none()

        qs = User.objects.filter(is_superuser=True)

        if self.q:
            qs = qs.filter(email__icontains=self.q)

        return qs
