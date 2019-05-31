# -*- coding: utf-8 -*-
import json

import falcon

from mcod.lib.encoders import DateTimeToISOEncoder


class BaseView(object):
    def handle(self, request, response, handler, *args, **kwargs):
        body = handler(request, response).run(*args, **kwargs)
        response.body = json.dumps(body, cls=DateTimeToISOEncoder)
        response.status = falcon.HTTP_200
        response.content_type = 'application/vnd.api+json'

    def handle_post(self, request, response, handler, *args, **kwargs):
        body = handler(request, response).run(*args, **kwargs)
        response.body = json.dumps(body, cls=DateTimeToISOEncoder)
        response.status = falcon.HTTP_201
        response.content_type = 'application/vnd.api+json'
