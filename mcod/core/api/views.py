# -*- coding: utf-8 -*-
from datetime import datetime
import falcon
from mcod import settings


class BaseView(object):

    csrf_exempt = False  # change to True to disable CSRF validation for concrete view.

    def handle(self, request, response, handler, *args, **kwargs):
        response.content_type = self.set_content_type(response, **kwargs)
        response.status = falcon.HTTP_200
        response.media = handler(request, response).run(*args, **kwargs)

    def handle_post(self, request, response, handler, *args, **kwargs):
        response.media = handler(request, response).run(*args, **kwargs)
        response.content_type = self.set_content_type(response, **kwargs)
        response.status = falcon.HTTP_201

    def handle_delete(self, request, response, handler, *args, **kwargs):
        handler(request, response).run(*args, **kwargs)
        response.content_type = None
        response.status = falcon.HTTP_204

    def handle_patch(self, request, response, handler, *args, **kwargs):
        response.content_type = self.set_content_type(response, **kwargs)
        response.status = falcon.HTTP_202
        response.media = handler(request, response).run(*args, **kwargs)

    def handle_bulk_patch(self, request, response, handler, *args, **kwargs):
        handler(request, response).run(*args, **kwargs)
        response.content_type = self.set_content_type(response, **kwargs)
        response.status = falcon.HTTP_202

    def handle_bulk_delete(self, request, response, handler, *args, **kwargs):
        handler(request, response).run(*args, **kwargs)
        response.content_type = self.set_content_type(response, **kwargs)
        response.status = falcon.HTTP_202

    def set_content_type(self, resp, **kwargs):
        return resp.content_type


class JsonAPIView(BaseView):
    def set_content_type(self, resp, **kwargs):
        if resp.content_type not in settings.JSONAPI_MIMETYPES:
            return settings.JSONAPI_MIMETYPES[0]

        return resp.content_type


class TabularView(BaseView):

    def handle(self, request, response, handler, *args, **kwargs):
        super().handle(request, response, handler, *args, **kwargs)
        # https://falcon.readthedocs.io/en/latest/user/recipes/output-csv.html
        response.downloadable_as = 'harmonogram-{}.{}'.format(
            datetime.today().strftime('%Y-%m-%d'),
            kwargs.get('export_format', 'csv'),
        )

    def set_content_type(self, resp, **kwargs):
        return settings.EXPORT_FORMAT_TO_MIMETYPE.get(kwargs.get('export_format', 'csv'), resp.content_type)


class RDFView(BaseView):
    def set_content_type(self, resp, rdf_format=None, **kwargs):
        if rdf_format:
            return settings.RDF_FORMAT_TO_MIMETYPE.get(rdf_format, None)

        if resp.content_type not in settings.RDF_MIMETYPES:
            return 'application/ld+json'

        return resp.content_type
