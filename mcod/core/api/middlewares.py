import json
from datetime import datetime

import elasticapm
import elasticapm.instrumentation.control
import falcon
from django.utils.translation import activate
from django.utils.translation.trans_real import (
    get_supported_language_variant,
    language_code_re,
    parse_accept_lang_header
)
from django_redis import get_redis_connection
from elasticapm.conf import constants
from elasticapm.utils.disttracing import TraceParent

from mcod import settings
from mcod.core.api.apm import get_data_from_response, get_data_from_request
from mcod.core.api.versions import VERSIONS
from mcod.core.utils import jsonapi_validator, route_to_name
from mcod.counters.lib import Counter
from mcod.lib.encoders import DateTimeToISOEncoder


class SearchHistoryMiddleware:
    def process_response(self, req, resp, resource, req_succeeded):
        if hasattr(req, 'user') and req.user.is_authenticated:
            if req.path in settings.SEARCH_HISTORY_PATHS \
                    and req.query_string not in settings.SEARCH_HISTORY_BLACKLISTED_QUERIES:
                con = get_redis_connection()
                key = f"search_history_user_{req.user.id}"
                con.lpush(key, req.url)


class ApiVersionMiddleware(object):
    def process_request(self, req, resp):
        current_version = max(VERSIONS)
        version = req.headers.get('X-API-VERSION', str(current_version))

        try:
            if version not in VERSIONS:
                raise ValueError
        except ValueError:
            raise falcon.HTTPBadRequest('Unsupported version',
                                        'Version provided in X-API-VERSION header is invalid.')

        req.api_version = version


class LocaleMiddleware(object):
    def get_language_from_header(self, header):
        for accept_lang, unused in parse_accept_lang_header(header):
            if accept_lang == '*':
                break

            if not language_code_re.search(accept_lang):
                continue

            try:
                return get_supported_language_variant(accept_lang)
            except LookupError:
                continue

        try:
            return get_supported_language_variant(settings.LANGUAGE_CODE)
        except LookupError:
            return settings.LANGUAGE_CODE

    def process_request(self, req, resp):
        accept_header = req.headers.get('ACCEPT-LANGUAGE', '')
        lang = self.get_language_from_header(accept_header)
        req.language = lang.lower()
        activate(req.language)

    def process_response(self, req, resp, resource, params):
        resp.append_header('Content-Language', req.language)


class CounterMiddleware(object):

    def process_response(self, req, resp, resource, req_succeeded):
        try:
            view, obj_id = req.relative_uri.split('?')[0].split('/')[1:]
            obj_id = int(obj_id)
        except ValueError:
            view, obj_id = None, None

        if view in settings.COUNTED_VIEWS:
            counter = Counter()
            counter.incr_view_count(view, obj_id)


class DebugMiddleware(object):
    def process_request(self, request, response):
        response.context.debug = True if request.params.get('debug') == 'yes' else False

        if response.context.debug:
            request.context.start_time = datetime.now()

    def process_response(self, request, response, resource, req_succeeded):
        if response.context.debug:
            duration = (datetime.now() - request.context.start_time).microseconds
            response_body = json.loads(response.body)
            valid, validated, errors = 'n/a', None, None
            if response.status == falcon.HTTP_200:
                valid, validated, errors = jsonapi_validator(response_body)

            body = {
                'status': response.status,
                'valid': 'ok' if valid else 'error',
                'duration': '{} ms'.format(duration / 1000),
                'query': getattr(response.context, 'query', {}),
                'errors': errors or [],
                'body': response_body,
                'data': validated
            }

            response.body = json.dumps(body, cls=DateTimeToISOEncoder)
            response.status = falcon.HTTP_200
            response.content_type = 'application/json'


class TraceMiddleware(object):
    def __init__(self, apm_client):
        self.client = apm_client

    def process_request(self, req, resp):
        if self.client and req.user_agent != 'mcod-heartbeat':
            if constants.TRACEPARENT_HEADER_NAME in req.headers:
                trace_parent = TraceParent.from_string(req.headers[constants.TRACEPARENT_HEADER_NAME])
            else:
                trace_parent = None

            self.client.begin_transaction("request", trace_parent=trace_parent)

    def process_response(self, req, resp, resource, req_succeeded=None):
        if self.client and req.user_agent != 'mcod-heartbeat':
            rule = route_to_name(req.uri_template, prefix='api', method=req.method)
            elasticapm.set_context(
                lambda: get_data_from_request(
                    req,
                    capture_body=self.client.config.capture_body in ("transactions", "all"),
                    capture_headers=self.client.config.capture_headers,
                ),
                "request",
            )
            elasticapm.set_context(
                lambda: get_data_from_response(resp, capture_headers=self.client.config.capture_headers), "response"
            )

            result = resp.status
            elasticapm.set_transaction_name(rule, override=False)
            if hasattr(req, 'user') and req.user.is_authenticated:
                elasticapm.set_user_context(email=req.user.email, user_id=req.user.id)

            elasticapm.set_transaction_result(result, override=False)
            # Instead of calling end_transaction here, we defer the call until the response is closed.
            # This ensures that we capture things that happen until the WSGI server closes the response.
            self.client.end_transaction(rule, result)
