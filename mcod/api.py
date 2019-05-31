#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

import django
import elasticapm
import falcon
from elasticapm.conf import setup_logging
from elasticapm.handlers.logging import LoggingHandler
from falcon import DEFAULT_MEDIA_TYPE
from falcon import media
from falcon.request import Request
from falcon.response import Response
from webargs import falconparser

from mcod import settings
from mcod.core.api import middlewares
from mcod.core.api.apm import get_client, get_data_from_request
from mcod.lib.errors import error_serializer, error_handler, error_422_handler, error_500_handler

logger = logging.getLogger("elasticapm.errors.client")

extra_handlers = {
    'application/vnd.api+json': media.JSONHandler()
}


class ApiApp(falcon.API):
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
            self.add_route(*route)

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


def get_api_app():
    from mcod.routes import routes
    app = ApiApp(middleware=[
        middlewares.DebugMiddleware(),
        middlewares.LocaleMiddleware(),
        middlewares.ApiVersionMiddleware(),
        middlewares.CounterMiddleware(),
        middlewares.SearchHistoryMiddleware(),
    ])

    app.add_error_handler(Exception, error_500_handler)
    app.add_error_handler(falcon.HTTPError, error_handler)
    app.add_error_handler(falcon.HTTPInternalServerError, error_500_handler)
    app.add_error_handler(falconparser.HTTPError, error_422_handler)
    app.add_error_handler(falcon.HTTPUnprocessableEntity, error_422_handler)
    app.set_error_serializer(error_serializer)
    app.add_routes(routes)
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
