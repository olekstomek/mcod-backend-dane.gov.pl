import json
import traceback
from uuid import uuid4

from django.utils.translation import gettext_lazy as _
from flatdict import FlatDict

from mcod import logger, settings
from mcod.core.api.jsonapi.serializers import ErrorsSchema
from mcod.lib.encoders import LazyEncoder
from mcod.lib.schemas import ErrorSchema


def update_content_type(request, response):
    if request.api_version == '1.0':
        response.content_type = 'application/json'
    else:
        response.content_type = 'application/vnd.api+json'


def error_serializer(req, resp, exc):
    resp.text = exc.to_json()
    update_content_type(req, resp)
    resp.append_header('Vary', 'Accept')


def _prepare_error(exc, error_data=None):
    error_data = error_data or {}
    _status = getattr(exc, 'status', None) or error_data.get('status') or ''
    _title = getattr(exc, 'title', None) or error_data.get('title') or ''
    _description = getattr(exc, 'description', None) or error_data.get('description') or ''
    _code = _status.lower().replace(' ', '_')
    _error_data = {}

    if error_data:
        _error_data.update(error_data)

    _error_data.update({
        'id': uuid4(),
        'title': _title or _status,
        'code': _code,
        'status': _status
    })

    if _description:
        _error_data['detail'] = _description

    return ErrorsSchema().dump({
        'errors': [_error_data, ]
    })


def error_handler(exc, req, resp, params):
    update_content_type(req, resp)
    resp.status = exc.status
    if req.api_version == '1.0':
        exc_data = {
            'title': exc.title,
            'description': exc.description,
            'code': getattr(exc, 'code') or 'error'
        }
        result = ErrorSchema().dump(exc_data)
        resp.text = json.dumps(result, cls=LazyEncoder)
    else:
        resp.text = json.dumps(_prepare_error(exc), cls=LazyEncoder)


def error_404_handler(exc, req, resp, params):
    update_content_type(req, resp)
    resp.status = exc.status

    if req.api_version == '1.0':
        exc_data = {
            'title': exc.title,
            'description': exc.description,
            'code': getattr(exc, 'code') or 'error'
        }
        result = ErrorSchema().dump(exc_data)
        resp.text = json.dumps(result, cls=LazyEncoder)
    else:
        error_data = {
            'detail': _('The requested resource could not be found')
        }

        resp.text = json.dumps(_prepare_error(exc, error_data=error_data), cls=LazyEncoder)


def error_500_handler(exc, req, resp, params):
    update_content_type(req, resp)
    resp.status = getattr(exc, 'status', '500 Internal Server Error')

    if req.api_version == '1.0':
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
        resp.text = json.dumps(result, cls=LazyEncoder)
    else:
        error_data = {
            'status': resp.status,
            'detail': getattr(exc, 'description', ' '.join(str(a).capitalize() for a in exc.args)),
            'title': getattr(exc, 'title', "Hmm, something goes wrong...")
        }
        error_data['meta'] = {
            'traceback': traceback.format_exc()
        }

        body = _prepare_error(exc, error_data)
        resp.text = json.dumps(body, cls=LazyEncoder)

    if settings.DEBUG and getattr(settings, "CONSOLE_LOG_ERRORS", False):
        logger.exception(exc)


def error_422_handler(exc, req, resp, params):
    update_content_type(req, resp)
    resp.status = exc.status

    if req.api_version == '1.0':
        exc_data = {
            'title': exc.title,
            'description': _('Field value error'),
            'code': getattr(exc, 'code') or 'entity_error'
        }
        if hasattr(exc, 'errors'):
            exc_data['errors'] = exc.errors

        result = ErrorSchema().dump(exc_data)
        resp.text = json.dumps(result, cls=LazyEncoder)
    else:
        _exc_code = exc.status.lower().replace(' ', '_')
        _errors = []
        if hasattr(exc, 'errors'):
            flat = FlatDict(exc.errors, delimiter='/')
            for field, errors in flat.items():
                if not isinstance(errors, list):
                    errors = [str(errors), ]

                for title in errors:
                    _error = {
                        'id': uuid4(),
                        'title': _('Field error'),
                        'detail': _(title),
                        'status': resp.status,
                        'code': getattr(exc, 'code') or _exc_code,
                        'source': {
                            'pointer': '/{}'.format(field)
                        }
                    }
                    _errors.append(_error)
        else:
            _error = {
                'id': uuid4(),
                'code': getattr(exc, 'code') or _exc_code,
                'title': exc.title,
                'detail': _('Field value error'),
                'status': resp.status
            }
            _errors.append(_error)

        result = ErrorsSchema().dump({
            'errors': _errors
        })

        resp.text = json.dumps(result, cls=LazyEncoder)
