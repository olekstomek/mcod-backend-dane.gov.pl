# -*- coding: utf-8 -*-
import marshmallow as ma
from collections import namedtuple
from smtplib import SMTPException
from functools import partial

import falcon
# from cache_memoize import cache_memoize
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.password_validation import validate_password as dj_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from mcod.academy.models import Course
from mcod.core.api.handlers import CreateOneHdlr, RetrieveOneHdlr, SearchHdlr, UpdateOneHdlr
from mcod.core.api.hooks import login_required
from mcod.core.api.views import JsonAPIView
from mcod.core.versioning import versioned
from mcod.laboratory.models import LabEvent
from mcod.lib.handlers import BaseHandler
from mcod.lib.jwt import get_auth_token
from mcod.lib.triggers import session_store
from mcod.schedules.models import Schedule
from mcod.suggestions.models import AcceptedDatasetSubmission
from mcod.tools.api.dashboard import DashboardMetaSerializer, DashboardSerializer
from mcod.users.documents import MeetingDoc
from mcod.users.forms import AdminLoginForm
from mcod.users.models import Meeting, Token
from mcod.users.deserializers import (
    ChangePasswordApiRequest,
    ConfirmResetPasswordApiRequest,
    LoginApiRequest,
    MeetingApiSearchRequest,
    RegistrationApiRequest,
    ResendActivationEmailApiRequest,
    ResetPasswordApiRequest,
    UserUpdateApiRequest,
)
from mcod.users.serializers import (
    ChangePasswordApiResponse,
    ConfirmResetPasswordApiResponse,
    LoginApiResponse,
    LogoutApiResponse,
    MeetingApiResponse,
    UserApiResponse,
    RegistrationApiResponse,
    ResendActivationEmailApiResponse,
    ResetPasswordApiResponse,
    VerifyEmailApiResponse,
)
from mcod.watchers.models import Subscription


User = get_user_model()


class LoginView(JsonAPIView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        database_model = get_user_model()
        deserializer_schema = LoginApiRequest
        serializer_schema = partial(LoginApiResponse, many=False)

        def _get_data(self, cleaned, *args, **kwargs):
            cleaned = cleaned['data']['attributes']
            cleaned['email'] = cleaned['email'].lower()
            try:
                user = User.objects.get(email=cleaned['email'], is_removed=False, is_permanently_removed=False)
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

            user = authenticate(request=self.request, **cleaned)

            if user is None:
                raise falcon.HTTPUnauthorized(
                    title='401 Unauthorized',
                    description=_('Invalid email or password'),
                    code='authorization_error'
                )

            if not hasattr(self.request, 'session'):
                self.request.session = session_store()

                self.request.META = {}
            login(self.request, user)
            self.request.session.save()
            user.token = get_auth_token(user, self.request.session.session_key)
            return user


class RegistrationView(JsonAPIView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        database_model = get_user_model()
        deserializer_schema = RegistrationApiRequest
        serializer_schema = RegistrationApiResponse

        def _get_data(self, cleaned, *args, **kwargs):
            data = cleaned['data']['attributes']
            if User.objects.filter(email__iexact=data['email']):
                raise falcon.HTTPForbidden(
                    title='403 Forbidden',
                    description=_('This e-mail is already used'),
                    code='email_already_used'
                )
            data['email'] = data['email'].lower()
            user = User.objects.create_user(**data)
            try:
                user.send_registration_email()
            except SMTPException:
                raise falcon.HTTPInternalServerError(
                    description=_('Email cannot be sent'),
                    code='email_send_error'
                )
            return user


class AccountView(JsonAPIView):
    @falcon.before(login_required)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_required)
    @versioned
    def on_put(self, request, response, *args, **kwargs):
        self.handle(request, response, self.PUT, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        serializer_schema = partial(UserApiResponse, many=False)
        include_default = ['institution']
        _includes = {
            'institution': 'organizations.Organization',
            'agent_institution': 'organizations.Organization',
            'agent_institution_main': 'organizations.Organization',
        }
        _include_map = {
            'agent_institution': 'agent_institutions_included',
            'agent_institution_main': 'agent_organization',
        }

        def clean(self, *args, **kwargs):
            self._get_instance(*args, **kwargs)
            return {}

        def _get_data(self, cleaned, *args, **kwargs):
            return self._get_instance(*args, **kwargs)

        def _get_instance(self, *args, **kwargs):
            instance = getattr(self, '_cached_instance', None)
            if not instance:
                self._cached_instance = self.request.user
            return self._cached_instance

    class PUT(UpdateOneHdlr):
        database_model = get_user_model()
        deserializer_schema = UserUpdateApiRequest
        serializer_schema = UserApiResponse

        def clean(self, *args, **kwargs):
            return super().clean(self.request.user.id, validators=None, *args, **kwargs)

        def _get_data(self, cleaned, *args, **kwargs):
            data = cleaned['data']['attributes']

            user = self.request.user
            for attr, val in data.items():
                setattr(user, attr, val)
            user.save(update_fields=list(data.keys()))
            user.refresh_from_db()
            return user


class DashboardView(JsonAPIView):
    @falcon.before(login_required)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, handler=self.GET, *args, **kwargs)

    class GET(BaseHandler):
        deserializer_schema = ma.Schema()
        serializer_schema = DashboardSerializer(many=False)
        meta_serializer = DashboardMetaSerializer(many=False)

        def _data(self, request, cleaned, *args, **kwargs):
            data = {
                "aggregations": self._get_aggregations(request.user),
            }
            if 'schedules' in data['aggregations']:
                notifications = request.user.schedule_dashboard_notifications
                data['aggregations']['schedules'].update({
                    'notifications': notifications,
                    'notifications_count': notifications.count(),
                })
            return data

        # @cache_memoize(60 * 2, args_rewrite=lambda self, user: (user.id, ))
        def _get_aggregations(self, user):
            result = {
                'subscriptions': self._get_user_subscriptions(user),
            }
            if user.has_access_to_academy_in_dashboard:
                result.update({
                    'academy': self._get_academy_aggregations()
                })

            if user.has_access_to_laboratory_in_dashboard:
                result.update({
                    'lab': self._get_laboratory_aggregations()
                })
            if user.has_access_to_suggestions_in_dashboard:
                result.update({
                    'suggestions': self._get_suggestions_aggregations()
                })
            if user.has_access_to_meetings_in_dashboard:
                result.update({
                    'meetings': self._get_meetings_aggregations()
                })
            schedules_aggregations = Schedule.get_dashboard_aggregations_for(user)
            if schedules_aggregations:
                result.update({'schedules': schedules_aggregations})

            result.update({
                'fav_charts': self._get_fav_charts_aggregations(user)
            })
            if user.is_superuser:
                result.update({
                    'analytical_tools': self._get_analytical_tools(),
                    'cms_url': settings.CMS_URL
                })
            return result

        @staticmethod
        def _get_user_subscriptions(user: User):
            return {
                "datasets": Subscription.objects.filter(
                    user=user,
                    watcher__object_name='datasets.Dataset',
                ).count(),
                "queries": user.subscriptions.filter(
                    watcher__object_name='query',
                ).count(),
            }

        @staticmethod
        def _get_laboratory_aggregations():
            return {
                'analyses': LabEvent.objects.filter(
                    event_type='analysis',
                ).count(),
                'researches': LabEvent.objects.filter(
                    event_type='research',
                ).count(),
            }

        @staticmethod
        def _get_meetings_aggregations():
            today = timezone.now().date()
            objs = Meeting.objects.published()
            return {
                'planned': objs.filter(start_date__gte=today).count(),
                'finished': objs.filter(start_date__lt=today).count(),
            }

        @staticmethod
        def _get_academy_aggregations():
            courses = Course.objects.with_schedule()
            return {
                state: courses.filter(
                    _course_state=state
                ).count()
                for state in Course.COURSE_STATES
            }

        @staticmethod
        def _get_suggestions_aggregations():
            objs = AcceptedDatasetSubmission.objects.filter(status__in=AcceptedDatasetSubmission.PUBLISHED_STATUSES)
            return {
                'active': objs.filter(is_active=True).count(),
                'inactive': objs.filter(is_active=False).count(),
            }

        @staticmethod
        def _get_fav_charts_aggregations(user: User):
            _default = {
                'slot-1': {},
                'slot-2': {}
            }
            fav_charts = user.fav_charts or {}
            _default.update(fav_charts)
            for key, item in _default.items():
                if item:
                    _default[key]['thumb_url'] = f'{settings.BASE_URL}/pn-apps/charts/{key}.png'

            return _default

        @staticmethod
        def _get_analytical_tools():
            return [{'name': 'Kibana', 'url': settings.KIBANA_URL}, {'name': 'Metabase', 'url': settings.METABASE_URL}]


class LogoutView(JsonAPIView):
    @falcon.before(login_required)
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        database_model = get_user_model()
        serializer_schema = LogoutApiResponse

        def _get_data(self, cleaned, *args, **kwargs):
            _user_id = self.request.user.id
            logout(self.request)
            return namedtuple('User', ['id', 'is_logged_out'])(_user_id, True)


class ResetPasswordView(JsonAPIView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)
        response.status = falcon.HTTP_200

    class POST(CreateOneHdlr):
        deserializer_schema = partial(ResetPasswordApiRequest, many=False)
        serializer_schema = partial(ResetPasswordApiResponse, many=False)
        database_model = get_user_model()

        def _get_data(self, cleaned, *args, **kwargs):
            data = cleaned['data']['attributes']
            try:
                user = self.database_model.objects.get(email=data['email'])
            except self.database_model.DoesNotExist:
                raise falcon.HTTPNotFound(
                    description=_('Account not found'),
                    code='account_not_found'
                )
            try:
                msgs_count = user.send_password_reset_email()
            except SMTPException:
                raise falcon.HTTPInternalServerError(
                    description=_('Email cannot be sent'),
                    code='email_send_error'
                )
            user.is_password_reset_email_sent = bool(msgs_count)
            return user


class ConfirmResetPasswordView(JsonAPIView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        database_model = get_user_model()
        deserializer_schema = ConfirmResetPasswordApiRequest
        serializer_schema = ConfirmResetPasswordApiResponse

        def _get_data(self, cleaned, *args, **kwargs):
            data = cleaned['data']['attributes']
            token = kwargs.get('token')
            try:
                token = Token.objects.get(token=token, token_type=1)
            except Token.DoesNotExist:
                raise falcon.HTTPNotFound()
            if not token.is_valid:
                raise falcon.HTTPBadRequest(
                    description=_('Expired token'),
                    code='expired_token'
                )
            token.user.set_password(data['new_password1'])
            token.user.save()
            token.invalidate()
            token.user.is_confirmed = True
            return token.user


class ChangePasswordView(JsonAPIView):
    @falcon.before(login_required)
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        database_model = get_user_model()
        deserializer_schema = ChangePasswordApiRequest
        serializer_schema = ChangePasswordApiResponse

        def _get_data(self, cleaned, *args, **kwargs):
            user = self.request.user
            data = cleaned['data']['attributes']
            is_valid = user.check_password(data['old_password'])
            if not is_valid:
                raise falcon.HTTPUnprocessableEntity(
                    description=_('Wrong password'),
                )
            try:
                dj_validate_password(data['new_password1'])
            except DjangoValidationError as e:
                raise falcon.HTTPUnprocessableEntity(
                    description=e.error_list[0].message,
                )
            if data['new_password1'] != data['new_password2']:
                raise falcon.HTTPUnprocessableEntity(
                    description=_('Passwords not match'),
                )
            user.set_password(data['new_password1'])
            user.save()
            user.is_password_changed = True
            return user


class VerifyEmailView(JsonAPIView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        database_model = get_user_model()
        serializer_schema = VerifyEmailApiResponse

        def clean(self, token, *args, **kwargs):
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

            return {}

        def _get_data(self, cleaned, token, *args, **kwargs):
            return namedtuple('Token', ['id', 'is_verified'])(token, True)


class ResendActivationEmailView(JsonAPIView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        database_model = get_user_model()
        deserializer_schema = ResendActivationEmailApiRequest
        serializer_schema = ResendActivationEmailApiResponse

        def _get_data(self, cleaned, *args, **kwargs):
            data = cleaned['data']['attributes']
            try:
                user = self.database_model.objects.get(email=data['email'])
            except self.database_model.DoesNotExist:
                raise falcon.HTTPNotFound(
                    description=_('Account not found'),
                    code='account_not_found'
                )
            try:
                msgs_count = user.resend_activation_email()
                user.is_activation_email_sent = bool(msgs_count)
                self.response.context.data = user
            except SMTPException:
                raise falcon.HTTPInternalServerError(
                    description=_('Email cannot be sent'),
                    code='email_send_error'
                )


class CustomAdminLoginView(DjangoLoginView):
    form_class = AdminLoginForm
    template_name = 'admin/login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_active and request.user.is_staff:
            # Already logged-in, redirect to admin index
            index_path = reverse('admin:index', current_app=settings.COMPONENT)
            return HttpResponseRedirect(index_path)
        return super().get(request, *args, **kwargs)


class MeetingsView(JsonAPIView):

    @falcon.before(login_required, roles=['admin', 'agent'])
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = MeetingApiSearchRequest
        serializer_schema = partial(MeetingApiResponse, many=True)
        search_document = MeetingDoc()
