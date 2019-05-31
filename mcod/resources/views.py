# -*- coding: utf-8 -*-

import json
from collections import namedtuple
from functools import partial
from uuid import uuid4

import falcon
from apispec import APISpec
from django.apps import apps
from django.template import loader

from mcod import settings
from mcod.core.api.handlers import SearchHdlr, RetrieveOneHdlr, CreateOneHdlr
from mcod.core.api.openapi.plugins import TabularDataPlugin
from mcod.core.api.versions import DOC_VERSIONS
from mcod.core.api.views import BaseView
from mcod.core.versioning import versioned
from mcod.counters.lib import Counter
from mcod.lib.encoders import DateTimeToISOEncoder
from mcod.lib.handlers import SearchHandler, RetrieveOneHandler
from mcod.resources.depricated.schemas import ResourcesList
from mcod.resources.depricated.serializers import ResourceSerializer, ResourcesMeta, ResourceDataSerializer
from mcod.resources.deserializers import ResourceApiRequest, ResourceApiSearchRequest, TableApiRequest, \
    TableApiSearchRequest, CreateCommentRequest
from mcod.resources.documents import ResourceDoc
from mcod.resources.serializers import ResourceApiResponse, CommentApiResponse, TableApiResponse
from mcod.resources.tasks import send_resource_comment


class ResourcesView(BaseView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/resources/resources_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(SearchHandler):
        meta_serializer = ResourcesMeta()
        deserializer_schema = ResourcesList()
        serializer_schema = ResourceSerializer(many=True)
        search_document = ResourceDoc()

    class GET(SearchHdlr):
        deserializer_schema = partial(ResourceApiSearchRequest)
        serializer_schema = partial(ResourceApiResponse, many=True)
        search_document = ResourceDoc()

        def _queryset_extra(self, queryset, *args, **kwargs):
            return queryset.filter('term', status='published')


class ResourceView(BaseView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/resources/resource_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        deserializer_schema = partial(ResourceApiRequest)
        database_model = apps.get_model('resources', 'Resource')
        serializer_schema = partial(ResourceApiResponse, many=False)

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_instance', None)
            if not instance:
                model = self.database_model
                try:
                    self._cached_instance = model.objects.get(pk=id, status="published")
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance

    class GET_1_0(RetrieveOneHandler):
        database_model = apps.get_model('resources', 'Resource')
        serializer_schema = ResourceSerializer(many=False, include_data=('dataset',))

        def _clean(self, request, id, *args, **kwargs):
            model = self.database_model
            try:
                return model.objects.get(pk=id, status="published")
            except model.DoesNotExist:
                raise falcon.HTTPNotFound


class ResourceTableView(BaseView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/tables/list_view.yml

        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(TableApiSearchRequest)
        database_model = apps.get_model('resources', 'Resource')
        serializer_schema = partial(TableApiResponse, many=True)

        def _queryset_extra(self, queryset, *args, **kwargs):
            return queryset.sort('_score', 'row_no')

        def _get_resource_instance(self, id):
            cached_resource = getattr(self, '_cached_resource', None)
            if not cached_resource:
                model = self.database_model
                try:
                    self._cached_resource = model.objects.get(pk=id, status="published")

                except model.DoesNotExist:
                    raise falcon.HTTPNotFound

                if not self._cached_resource.tabular_data:
                    raise falcon.HTTPNotFound

            return self._cached_resource

        def _get_data(self, cleaned, id, *args, **kwargs):
            resource = self._get_resource_instance(id)

            self.search_document = resource.tabular_data.doc

            schema_cls = TableApiResponse
            _fields = resource.tabular_data.get_api_fields()
            schema_cls.opts.attrs_schema._declared_fields = _fields
            self.serializer_schema = partial(schema_cls, many=True)
            if resource.tabular_data and resource.tabular_data.available:
                return super()._get_data(cleaned, id, *args, **kwargs)

            raise falcon.HTTPNotFound

        def _get_meta(self, cleaned, id, *args, **kwargs):
            resource = self._get_resource_instance(id)
            if resource.tabular_data and resource.tabular_data.available:
                return dict(
                    headers_map=resource.tabular_data.headers_map,
                    data_schema=resource.tabular_data.get_schema(use_aliases=True)
                )
            return {}

    class GET_1_0(RetrieveOneHandler):
        database_model = apps.get_model('resources', 'Resource')
        serializer_schema = ResourceDataSerializer(many=False)

        def _clean(self, request, id, *args, **kwargs):
            model = self.database_model
            try:
                return model.objects.get(pk=id, status="published")
            except model.DoesNotExist:
                raise falcon.HTTPNotFound

        def _data(self, request, cleaned, *args, **kwargs):
            if cleaned.data_is_valid == 'SUCCESS' and cleaned.show_tabular_view:
                try:
                    headers_map = cleaned.tabular_data.headers_map
                    data = []
                    for result in cleaned.tabular_data.iter(from_=0, size=1000):
                        data.append([getattr(result, attr) for attr in headers_map.values()])

                    return {
                        'id': cleaned.id,
                        'schema': cleaned.tabular_data.schema,
                        'headers': list(headers_map.keys()),
                        'data': data
                    }

                except Exception:
                    return {}


class ResourceTableRowView(BaseView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/tables/single_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        deserializer_schema = partial(TableApiRequest)
        serializer_schema = partial(TableApiResponse, many=False)
        database_model = apps.get_model('resources', 'Resource')

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_instance', None)
            if not instance:
                model = self.database_model
                try:
                    self._cached_instance = model.objects.get(pk=id, status="published")
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance

        def _get_data(self, cleaned, id, row_id, *args, **kwargs):
            resource = self._get_instance(id, *args, **kwargs)
            self.search_document = resource.tabular_data.doc

            schema_cls = TableApiResponse
            _fields = resource.tabular_data.get_api_fields()
            schema_cls.opts.attrs_schema._declared_fields = _fields
            self.serializer_schema = partial(schema_cls, many=True)
            if resource.tabular_data and resource.tabular_data.available:
                return self.search_document.get(row_id)

            raise falcon.HTTPNotFound

        def _get_meta(self, cleaned, id, *args, **kwargs):
            resource = self._get_instance(id, *args, **kwargs)
            if resource.tabular_data and resource.tabular_data.available:
                return dict(
                    headers_map=resource.tabular_data.headers_map,
                    data_schema=resource.tabular_data.get_schema(use_aliases=True)
                )
            return {}


class ResourceCommentsView(BaseView):
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        deserializer_schema = partial(CreateCommentRequest)
        serializer_schema = partial(CommentApiResponse, many=False)
        database_model = apps.get_model('resources', 'Resource')

        def _get_resource(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_resource', None)
            if not instance:
                model = self.database_model
                try:
                    self._cached_resource = self.database_model.objects.get(pk=id, status="published")
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_resource

        def clean(self, id, *args, **kwargs):
            cleaned = super().clean(id, *args, **kwargs)
            self._get_resource(id, *args, **kwargs)
            return cleaned

        def _get_data(self, cleaned, id, *args, **kwargs):
            attrs = cleaned['data']['attributes']
            send_resource_comment.s(id, attrs['comment']).apply_async(countdown=1)
            result = namedtuple('Comment', ['id', 'comment', 'resource'])(
                str(uuid4()),
                attrs['comment'],
                self._get_resource(id, *args, **kwargs)
            )
            return result


class ResourceFileDownloadView(object):
    def on_get(self, request, response, id, *args, **kwargs):
        Resource = apps.get_model('resources', 'Resource')
        try:
            resource = Resource.objects.get(pk=id)
        except Resource.DoesNotExist:
            raise falcon.HTTPNotFound

        if not resource.type == 'file':
            raise falcon.HTTPNotFound

        if not resource.file_url:
            raise falcon.HTTPNotFound

        counter = Counter()
        counter.incr_download_count(id)

        response.location = resource.file_url
        response.status = falcon.HTTP_301


class ResourceTableSpecView(object):
    def on_get(self, req, resp, id, version=None):
        version = version or str(max(DOC_VERSIONS))

        if version and version not in DOC_VERSIONS:
            raise falcon.HTTPBadRequest(description='Unsupported API version')

        Resource = apps.get_model('resources', 'Resource')
        try:
            resource = Resource.objects.get(pk=id)
        except Resource.DoesNotExist:
            raise falcon.HTTPNotFound

        if not resource.tabular_data_schema:
            raise falcon.HTTPNotFound

        if not resource.tabular_data.available:
            raise falcon.HTTPNotFound

        template = loader.get_template('docs/tables/description.html')
        context = {
            'resource': resource,
            'headers_map': dict(resource.tabular_data.headers_map)
        }
        description = template.render(context)

        spec = APISpec(
            title=resource.title_truncated,
            version=version,
            openapi_version="3.0.0",
            plugins=[TabularDataPlugin(version)],
            info={
                'description': description,
            }
        )

        schema_cls = TableApiResponse
        _fields = resource.tabular_data.get_api_fields()
        schema_cls.opts.attrs_schema._declared_fields = _fields

        spec.components.schema('Rows', schema_cls=schema_cls, many=True)
        spec.components.schema('Row', schema_cls=schema_cls, many=False)
        spec.path(path='/resources/%s/data' % resource.id, resource=ResourceTableView)
        spec.path(path='/resources/%s/data/{id}' % resource.id, resource=ResourceTableRowView)

        resp.body = json.dumps(spec.to_dict(), cls=DateTimeToISOEncoder)
        resp.status = falcon.HTTP_200


class ResourceSwaggerView(object):
    def on_get(self, request, response, id):
        Resource = apps.get_model('resources', 'Resource')
        try:
            resource = Resource.objects.get(pk=id)
        except Resource.DoesNotExist:
            raise falcon.HTTPNotFound

        template = loader.get_template('swagger_ui/index.html')
        versions = sorted(DOC_VERSIONS, reverse=True)
        spec_url_mask = '{}/resources/{}/data/spec/{}'
        context = {
            'spec_url': spec_url_mask.format(settings.API_URL, id, str(versions[0])),
            'spec_urls': [
                {'url': spec_url_mask.format(settings.API_URL, id, str(version)),
                 'name': 'DANE.GOV.PL - {} API v{}'.format(resource.title_truncated, str(version))
                 } for version in versions
            ],
            'custom_css': 'custom.css'
        }

        response.status = falcon.HTTP_200
        response.content_type = 'text/html'
        response.body = template.render(context)


class ResourceDownloadCounter(object):
    def on_put(self, req, resp, id=None, **kwargs):
        if id:
            counter = Counter()
            counter.incr_download_count(id)
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        resp.body = json.dumps({}, cls=DateTimeToISOEncoder)
