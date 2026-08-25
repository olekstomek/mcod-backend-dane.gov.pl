import json
import logging
from typing import Any, Dict, Iterable, List, Mapping, Tuple, Union
from uuid import uuid4

import falcon.request
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from falcon import HTTP_500, HTTPError, Response

from mcod.core.api.jsonapi.serializers import ErrorsSchema
from mcod.lib.encoders import LazyEncoder
from mcod.lib.schemas import ErrorSchema

logger = logging.getLogger("mcod")


def _is_version_one(request: falcon.request.Request) -> bool:
    return getattr(request, "api_version", None) == "1.0"


def update_content_type(request: falcon.request.Request, response: Response):
    if _is_version_one(request):
        response.content_type = "application/json"
    else:
        response.content_type = "application/vnd.api+json"


def error_serializer(req, resp, exc):
    resp.text = exc.to_json()
    update_content_type(req, resp)
    resp.append_header("Vary", "Accept")


def error_handler(
    request: falcon.request.Request,
    response: Response,
    exc: Exception,
    params: Any,
) -> None:
    update_content_type(request, response)
    response_status: str = getattr(exc, "status", HTTP_500)

    default_error_msg = _("An unexpected error occurred. Please try again later.")

    if _is_version_one(request):
        exc_data = {
            "title": default_error_msg,
            "description": default_error_msg,
            "code": getattr(exc, "code", None) or "server_error",
        }
        body: Dict = ErrorSchema().dump(exc_data)

    else:
        exc_data = {
            "jsonapi": {"version": "1.4"},
            "errors": [
                {
                    "id": uuid4(),
                    "status": response_status,
                    "code": response_status.lower().replace(" ", "_"),
                    "title": default_error_msg,
                    "detail": default_error_msg,
                },
            ],
        }
        body: Dict = ErrorsSchema().dump(exc_data)

    response.text = json.dumps(body, cls=LazyEncoder)
    response.status = response_status

    if settings.DEBUG or settings.LOG_ALL_API_EXCEPTIONS:
        logger.exception(exc)


def error_404_handler(
    request: falcon.request.Request, response: Response, exc: falcon.HTTPNotFound, params: Dict[str, Any]
) -> None:
    update_content_type(request, response)
    response.status = exc.status

    if _is_version_one(request):
        exc_data = {
            "title": exc.title,
            "description": exc.description,
            "code": getattr(exc, "code") or "error",
        }
        result = ErrorSchema().dump(exc_data)
        response.text = json.dumps(result, cls=LazyEncoder)
    else:
        _title = _("The requested resource could not be found")
        _code = exc.status.lower().replace(" ", "_")
        error_body = {
            "id": uuid4(),
            "status": exc.status,
            "code": _code,
            "title": _title,
            "detail": _title,
        }
        if exc.title:
            error_body["title"] = exc.title
        if exc.description:
            error_body["detail"] = exc.description
        result = ErrorsSchema().dump(
            {
                "jsonapi": {"version": "1.4"},
                "errors": [
                    error_body,
                ],
            }
        )
        response.text = json.dumps(result, cls=LazyEncoder)


def _prepare_exception_for_14(
    request: falcon.request.Request, response: Response, exc: Exception, **override_fields: str
) -> dict:
    _api_version = getattr(request, "api_version", "1.4")
    _status = getattr(exc, "status", HTTP_500)
    _code = _status.lower().replace(" ", "_")
    error_body = {
        "id": uuid4(),
        "status": _status,
        "code": _code,
        "title": _("An unexpected error occurred. Please try again later."),
        "detail": _("An unexpected error occurred. Please try again later."),
    }
    error_body.update(override_fields)
    return ErrorsSchema().dump(
        {
            "jsonapi": {"version": _api_version},
            "errors": [
                error_body,
            ],
        }
    )


def _flatten_errors(data: Dict[Any, Any], prefix: str = "") -> List[Tuple[str, Any]]:
    """Recursively flattens a nested dictionary of errors into a flat list of paths and values."""
    items: List[Tuple[str, Any]] = []
    for key, value in data.items():
        new_prefix = f"{prefix}/{key}" if prefix else str(key)
        if isinstance(value, dict):
            items.extend(_flatten_errors(value, new_prefix))
        else:
            items.append((new_prefix, value))
    return items


def error_422_handler(request: falcon.request.Request, response: Response, exc: HTTPError, params):
    update_content_type(request, response)
    response.status = exc.status

    if _is_version_one(request):
        exc_data = {
            "title": exc.title,
            "description": _("Field value error"),
            "code": getattr(exc, "code") or "entity_error",
        }
        if hasattr(exc, "errors"):
            exc_data["errors"] = exc.errors

        result = ErrorSchema().dump(exc_data)
        response.text = json.dumps(result, cls=LazyEncoder)
    else:
        _exc_code = exc.status.lower().replace(" ", "_")
        _errors = []
        if hasattr(exc, "errors") and isinstance(exc.errors, dict):
            for field, errors in _flatten_errors(exc.errors):
                if not isinstance(errors, list):
                    errors = [
                        str(errors),
                    ]

                for title in errors:
                    _error = {
                        "id": uuid4(),
                        "title": _("Field error"),
                        "detail": _(title),
                        "status": response.status,
                        "code": getattr(exc, "code") or _exc_code,
                        "source": {"pointer": "/{}".format(field)},
                    }
                    _errors.append(_error)
        else:
            _error = {
                "id": uuid4(),
                "code": getattr(exc, "code") or _exc_code,
                "title": exc.title,
                "detail": _("Field value error"),
                "status": response.status,
            }
            _errors.append(_error)
        result = ErrorsSchema().dump({"errors": _errors})
        response.text = json.dumps(result, cls=LazyEncoder)


def http_error_handler(
    request: falcon.request.Request,
    response: Response,
    exc: HTTPError,
    params: Any,
) -> None:
    update_content_type(request, response)
    response_status: str = exc.status

    # Extend response headers from exc
    exc_headers: Union[Mapping[str, str], Iterable[Tuple[str, str]], None] = exc.headers
    if exc_headers:
        response.set_headers(exc_headers)

    default_error_msg = _("An unexpected error occurred. Please try again later.")

    exc_title: str = exc.title or default_error_msg
    exc_description: str = exc.description or default_error_msg
    exc_code: str = str(exc.code) if exc.code else "error"

    if _is_version_one(request):
        exc_data = {
            "title": exc_title,
            "description": exc_description,
            "code": exc_code,
        }
        body: Dict = ErrorSchema().dump(exc_data)

    else:
        exc_data = {
            "jsonapi": {"version": "1.4"},
            "errors": [
                {
                    "id": uuid4(),
                    "status": response_status,
                    "code": response_status.lower().replace(" ", "_"),
                    "title": exc_title,
                    "detail": exc_description,
                },
            ],
        }
        body: Dict = ErrorsSchema().dump(exc_data)

    response.text = json.dumps(body, cls=LazyEncoder)
    response.status = response_status
