import json
import logging
import os
from functools import partial

import django
import elasticapm
import falcon
import sentry_sdk
from elasticapm.conf import setup_logging
from elasticapm.handlers.logging import LoggingHandler
from falcon import DEFAULT_MEDIA_TYPE
from falcon.media import JSONHandler
from falcon.request import Request
from falcon.response import Response
from falcon_caching import Cache as BaseCache
from falcon_limiter import Limiter
from webargs import falconparser

from mcod import settings
from mcod.core.api import middlewares
from mcod.core.api.apm import get_client, get_data_from_request
from mcod.core.api.converters import ExportFormatConverter, RDFFormatConverter
from mcod.core.api.media import ExportHandler, RDFHandler, SparqlHandler, XMLHandler, ZipHandler
from mcod.core.api.utils.json_encoders import APIEncoder
from mcod.core.utils import get_limiter_key
from mcod.lib.errors import (
    error_404_handler,
    error_422_handler,
    error_500_handler,
    error_handler,
    error_serializer,
)

logger = logging.getLogger("elasticapm.errors.client")

jsonapi_handler = JSONHandler(
    dumps=partial(json.dumps, cls=APIEncoder)
)

extra_handlers = {
    # JSON:API
    'application/vnd.api+json': jsonapi_handler,
    'application/vnd.api+json; ext=bulk': jsonapi_handler,
    # XML
    'application/xml': XMLHandler(),
    # other
    'text/csv': ExportHandler(),
    'text/tsv': ExportHandler(),
    'text/tab-separated-values': ExportHandler(),
    'application/vnd.ms-excel': ExportHandler(),
    'application/sparql-results+json': SparqlHandler(),
    'application/sparql-results+xml': SparqlHandler(),
    'application/zip': ZipHandler()
}


extra_handlers.update(
    {mt: RDFHandler() for mt in set(settings.RDF_FORMAT_TO_MIMETYPE.values())}
)


class ApiApp(falcon.App):
    def __init__(self, media_type=DEFAULT_MEDIA_TYPE,
                 request_type=Request, response_type=Response,
                 middleware=None, router=None,
                 independent_middleware=False):
        self.apm_client = get_client()
        if self.apm_client:
            logging_level = getattr(settings, 'API_LOG_LEVEL', 'DEBUG')
            setup_logging(LoggingHandler(self.apm_client, level=logging_level))

            if self.apm_client.config.instrument:
                elasticapm.instrumentation.control.instrument()
                middleware.insert(0, middlewares.TraceMiddleware(self.apm_client))

        super().__init__(
            media_type=media_type,
            request_type=request_type,
            response_type=response_type,
            middleware=middleware,
            router=router,
            independent_middleware=independent_middleware
        )

    def add_routes(self, routes):
        for route in routes:
            try:
                suffix = route[2]
                self.add_route(*route[:2], suffix=suffix)
            except IndexError:
                self.add_route(*route)

    def add_suffixed_routes(self, suffixed_routes):
        for suffix, routes in suffixed_routes.items():
            for route in routes:
                self.add_route(*route, suffix=suffix)

    def _handle_exception(self, req, resp, exc, params):
        if self.apm_client:
            self.apm_client.capture_exception(
                exc_info=True,
                context={
                    "request": get_data_from_request(
                        req,
                        capture_body=self.apm_client.config.capture_body in ("errors", "all"),
                        capture_headers=self.apm_client.config.capture_headers,
                    )
                }
            )
        return super()._handle_exception(req, resp, exc, params)


class Cache(BaseCache):
    """Cache which uses custom version of middleware."""
    @property
    def middleware(self):
        return middlewares.FalconCacheMiddleware(self.cache, self.config)


app_cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_EVICTION_STRATEGY': 'time-based',
    'CACHE_KEY_PREFIX': 'falcon-cache',
    'CACHE_REDIS_URL': settings.REDIS_URL,
})  # https://falcon-caching.readthedocs.io/en/stable/


limiter = Limiter(
    key_func=get_limiter_key,
    default_limits=settings.FALCON_LIMITER_DEFAULT_LIMITS,
    config={
        'RATELIMIT_KEY_PREFIX': 'falcon-limiter',
        'RATELIMIT_STORAGE_URL': settings.REDIS_URL,
    }
)


def get_api_app():
    from mcod.routes import routes

    os.environ.setdefault("COMPONENT", "api")
    if settings.ENABLE_SENTRY:
        sentry_sdk.init(**settings.SENTRY_SDK_KWARGS['api'])

    _middlewares = [
        middlewares.ContentTypeMiddleware(),
        middlewares.DebugMiddleware(),
        middlewares.LocaleMiddleware(),
        middlewares.ApiVersionMiddleware(),
        middlewares.CounterMiddleware(),
        middlewares.SearchHistoryMiddleware(),
    ]

    if settings.ENABLE_CSRF:
        _middlewares.append(middlewares.CsrfMiddleware())
    if settings.FALCON_LIMITER_ENABLED:
        _middlewares.append(limiter.middleware)
    if settings.FALCON_CACHING_ENABLED:
        _middlewares.append(app_cache.middleware)

    app = ApiApp(middleware=_middlewares)

    app.router_options.converters['export_format'] = ExportFormatConverter
    app.router_options.converters['rdf_format'] = RDFFormatConverter
    app.add_error_handler(Exception, error_500_handler)
    app.add_error_handler(falcon.HTTPError, error_handler)
    app.add_error_handler(falcon.HTTPNotFound, error_404_handler)
    app.add_error_handler(falcon.HTTPInternalServerError, error_500_handler)
    app.add_error_handler(falconparser.HTTPError, error_422_handler)
    app.add_error_handler(falcon.HTTPUnprocessableEntity, error_422_handler)
    app.set_error_serializer(error_serializer)
    app.add_routes(routes)
    app.add_sink(lambda req, resp: setattr(resp, 'media', {'data': None}), '/ping')
    app.add_static_route(settings.STATIC_URL, settings.STATIC_ROOT)
    app.add_static_route(settings.MEDIA_URL, settings.MEDIA_ROOT)
    app.req_options.strip_url_path_trailing_slash = True
    app.req_options.media_handlers.update(extra_handlers)
    app.resp_options.media_handlers.update(extra_handlers)
    return app


django.setup()
app = get_api_app()

if __name__ == '__main__':
    from werkzeug.serving import run_simple

    run_simple('0.0.0.0', 8000, app, use_reloader=True)
