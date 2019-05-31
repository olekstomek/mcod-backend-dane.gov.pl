# -*- coding: utf-8 -*-
from importlib import import_module

import falcon
from django.contrib.auth import get_user
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from falcon.hooks import _wrap_with_after, _wrap_with_before

from mcod import settings
from mcod.lib.jwt import decode_jwt_token

session_store = import_module(settings.SESSION_ENGINE).SessionStore


class TriggerMeta(type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace)
        if 'Meta' not in namespace:
            cls.Meta = type('Meta', (type,), {'abstract': False})
        if not hasattr(cls.Meta, 'abstract'):
            cls.Meta.abstract = False

        if not cls.Meta.abstract:
            if not ('execute' in namespace and callable(namespace['execute'])):
                raise ImproperlyConfigured('Class must implement execute method')

        return cls


class Trigger(metaclass=TriggerMeta):
    def __init__(self, *func_args, **func_kwargs):
        self.func_args = func_args
        self.func_kwargs = func_kwargs

    class Meta:
        abstract = True


class ExecBefore(Trigger):
    def wrap(self, obj):
        return _wrap_with_before(obj, self.execute, self.func_args, self.func_kwargs)

    class Meta:
        abstract = True


class ExecAfter(Trigger):
    def wrap(self, obj):
        return _wrap_with_after(obj, self.execute, self.func_args, self.func_kwargs)

    class Meta:
        abstract = True


class LoginRequired(ExecBefore):
    def execute(self, req, resp, params):
        auth_header = req.get_header('Authorization')

        if not auth_header:
            raise falcon.HTTPUnauthorized(
                title='401 Unauthorized',
                description=_('Missing authorization header'),
                code='token_missing'
            )
        user_payload = decode_jwt_token(auth_header)['user']
        if not set(('session_key', 'email')) <= set(user_payload):
            raise falcon.HTTPUnauthorized(
                title='401 Unauthorized',
                description=_('Invalid authorization header'),
                code='token_error'
            )
        req.session = session_store(user_payload['session_key'])
        user = get_user(req)
        if not user or (hasattr(user, 'is_anonymous') and user.is_anonymous):
            raise falcon.HTTPUnauthorized(
                title='401 Unauthorized',
                description=_('Incorrect login data'),
                code='authentication_error'
            )
        if user.email != user_payload['email']:
            raise falcon.HTTPUnauthorized(
                title='401 Unauthorized',
                description=_('Incorrect login data'),
                code='authentication_error'
            )
        if user.state != 'active':
            if user.state not in settings.USER_STATE_LIST or user.state == 'deleted':
                raise falcon.HTTPUnauthorized(
                    title='401 Unauthorized',
                    description=_('Cannot login'),
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

        req.user = user


class LoginOptional(ExecBefore):
    def execute(self, req, resp, params):
        auth_header = req.get_header('Authorization')
        if not auth_header:
            req.user = AnonymousUser()
            return

        try:
            user_payload = ()
            user_payload = decode_jwt_token(auth_header)['user']
        except Exception:
            pass

        if not set(('session_key', 'email')) <= set(user_payload):
            req.user = AnonymousUser()
            return

        req.session = session_store(user_payload['session_key'])
        user = get_user(req)
        if user != AnonymousUser() and any((not user, user.email != user_payload['email'], user.state != 'active')):
            user = AnonymousUser()
        req.user = user
