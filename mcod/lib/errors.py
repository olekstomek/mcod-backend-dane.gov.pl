# -*- coding: utf-8 -*-
import json
import traceback

from django.utils.translation import gettext_lazy as _

from mcod import settings
from mcod.lib.encoders import LazyEncoder
from mcod.lib.schemas import ErrorSchema


def error_serializer(req, resp, exc):
    resp.body = exc.to_json()
    resp.content_type = 'application/json'
    resp.append_header('Vary', 'Accept')


def error_handler(exc, req, resp, params):
    resp.status = exc.status
    exc_data = {
        'title': exc.title,
        'description': exc.description,
        'code': getattr(exc, 'code') or 'error'
    }
    result = ErrorSchema().dump(exc_data)
    resp.body = json.dumps(result, cls=LazyEncoder)


def error_500_handler(exc, req, resp, params):
    resp.status = getattr(exc, 'status', '500 Internal Server Error')
    description = getattr(exc, 'description', ' '.join(a.capitalize() for a in exc.args))
    title = getattr(exc, 'title', "Hmm, something goes wrong...")
    code = getattr(exc, 'code', None)
    exc_data = {
        'title': title,
        'description': description or 'There was an unexpected error. Please try again later.',
        'code': code or 'server_error'
    }
    if settings.DEBUG:
        exc_data['traceback'] = traceback.format_exc()
    result = ErrorSchema().dump(exc_data)
    resp.body = json.dumps(result, cls=LazyEncoder)


def error_422_handler(exc, req, resp, params):
    resp.status = exc.status
    exc_data = {
        'title': exc.title,
        'description': _('Field value error'),
        'code': getattr(exc, 'code') or 'entity_error'
    }
    if hasattr(exc, 'errors'):
        exc_data['errors'] = exc.errors

    result = ErrorSchema().dump(exc_data)
    resp.body = json.dumps(result, cls=LazyEncoder)
