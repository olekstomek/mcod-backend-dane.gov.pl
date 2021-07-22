# -*- coding: utf-8 -*-
import os
import json
import falcon

from mcod import settings
from mcod.lib.docs.apispecs import rest_spec, rpc_spec
from mcod.lib.docs.tools import generate_apispec


class ApispecResource(object):
    def __init__(self, app):
        self.app = app


class RestApispecResource(ApispecResource):
    def on_get(self, request, response):
        spec = generate_apispec(self.app, rest_spec, start_line=settings.REST_APISPEC_START_LINE)
        response.status = falcon.HTTP_200
        response.body = json.dumps(spec.to_dict())


class RPCApispecResource(ApispecResource):
    def on_get(self, request, response):
        spec = generate_apispec(self.app, rpc_spec, start_line=settings.RPC_APISPEC_START_LINE)
        response.status = falcon.HTTP_200
        response.body = json.dumps(spec.to_dict())


class SwaggerResource(object):
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        # resp.status = 200
        resp.content_type = 'text/html'
        with open(os.path.join(settings.SWAGGER_ROOT, 'index.html'), 'r') as f:
            resp.body = f.read()
