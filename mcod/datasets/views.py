# -*- coding: utf-8 -*-
from functools import partial

import falcon
from dal import autocomplete
from django.apps import apps
from elasticsearch_dsl import Q, A
from django.conf import settings
from django.utils.translation import get_language

from mcod.core.api.handlers import (
    BaseHdlr, SearchHdlr, RetrieveOneHdlr, CreateOneHdlr,
    SubscriptionSearchHdlr, ShaclMixin
)
from mcod.core.api.hooks import login_optional
from mcod.core.api.views import JsonAPIView, RDFView, BaseView
from mcod.core.versioning import versioned
from mcod.datasets.deserializers import (
    DatasetApiRequest,
    DatasetApiSearchRequest,
    CreateCommentRequest,
    CatalogRdfApiRequest
)
from mcod.datasets.documents import DatasetDocumentActive
from mcod.datasets.handlers import DatasetResourcesMetadataViewHandler
from mcod.datasets.models import Dataset
from mcod.datasets.serializers import DatasetApiResponse, CommentApiResponse, DatasetRDFResponseSchema
from mcod.resources.deserializers import ResourceApiSearchRequest
from mcod.resources.documents import ResourceDocumentActive
from mcod.resources.serializers import ResourceApiResponse


class DatasetSearchView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/datasets/datasets_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SubscriptionSearchHdlr):
        deserializer_schema = partial(DatasetApiSearchRequest, many=False)
        serializer_schema = partial(DatasetApiResponse, many=True)
        search_document = DatasetDocumentActive()
        include_default = ['institution']


class DatasetApiView(JsonAPIView):
    @versioned
    @falcon.before(login_optional)
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/datasets/dataset_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        deserializer_schema = partial(DatasetApiRequest)
        database_model = apps.get_model('datasets', 'Dataset')
        serializer_schema = partial(DatasetApiResponse, many=False)
        include_default = ['institution', 'resource']


class CatalogRDFView(RDFView):
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(ShaclMixin, SearchHdlr):
        deserializer_schema = partial(CatalogRdfApiRequest, many=False)
        serializer_schema = partial(DatasetRDFResponseSchema, many=True)
        search_document = DatasetDocumentActive()

        def _queryset_extra(self, queryset, *args, **kwargs):
            queryset.aggs.metric('catalog_modified', A('max', field='last_modified_resource'))
            return queryset

        def serialize(self, *args, **kwargs):
            cleaned = getattr(self.request.context, 'cleaned_data', {})
            if self.use_rdf_db():
                store = self.get_sparql_store()
                return store.get_catalog(**cleaned)
            result = self._get_data(cleaned, *args, **kwargs)
            self.serializer.context['datasource'] = 'es'
            return self.serializer.dump(result)


class DatasetRDFView(RDFView):
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(ShaclMixin, RetrieveOneHdlr):
        deserializer_schema = partial(DatasetApiRequest)
        database_model = apps.get_model('datasets', 'Dataset')
        serializer_schema = partial(DatasetRDFResponseSchema, many=False)

        def serialize(self, *args, **kwargs):
            if self.use_rdf_db():
                store = self.get_sparql_store()
                return store.get_dataset_graph(**kwargs)
            cleaned = getattr(self.request.context, 'cleaned_data', {})
            dataset = self._get_data(cleaned, *args, **kwargs)
            self.serializer.context['datasource'] = 'db'
            return self.serializer.dump(dataset)


class DatasetResourceSearchApiView(JsonAPIView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/datasets/dataset_resources_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(ResourceApiSearchRequest, many=False)
        serializer_schema = partial(ResourceApiResponse, many=True)
        search_document = ResourceDocumentActive()

        def _queryset_extra(self, queryset, id=None, **kwargs):
            if id:
                queryset = queryset.query("nested", path="dataset",
                                          query=Q("term", **{'dataset.id': id}))
            return queryset.filter('term', status=Dataset.STATUS.published)


class DatasetCommentsView(JsonAPIView):
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        deserializer_schema = CreateCommentRequest
        serializer_schema = partial(CommentApiResponse, many=False)
        database_model = apps.get_model('datasets', 'Dataset')

        def _get_resource(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_resource', None)
            if not instance:
                try:
                    self._cached_resource = self.database_model.objects.get(pk=id, status="published")
                except self.database_model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_resource

        def clean(self, id, *args, **kwargs):
            cleaned = super().clean(id, *args, **kwargs)
            self._get_resource(id, *args, **kwargs)
            return cleaned

        def _get_data(self, cleaned, id, *args, **kwargs):
            data = cleaned['data']['attributes']
            model = apps.get_model('suggestions.DatasetComment')
            self.response.context.data = model.objects.create(dataset_id=id, **data)


class DatasetAutocompleteAdminView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        user = self.request.user

        if not user.is_authenticated:
            return Dataset.objects.none()

        qs = Dataset.objects.filter(status=Dataset.STATUS.published)

        if not user.is_superuser:
            qs = qs.filter(organization_id__in=user.organizations.all())

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return qs


class DatasetResourcesMetadataCsvView(BaseView):

    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(DatasetResourcesMetadataViewHandler):

        def _get_queryset(self, cleaned, *args, **kwargs):
            return self.database_model.objects.filter(dataset_id=kwargs['id'])

    def on_get_catalog(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GETCatalog, *args, **kwargs)

    class GETCatalog(BaseHdlr):

        def serialize(self, *args, **kwargs):
            try:
                with open(f'{settings.DATASET_CSV_CATALOG_MEDIA_ROOT}/{get_language()}/katalog.csv', 'rb') as f:
                    catalog_file = f.read()
            except FileNotFoundError:
                raise falcon.HTTPNotFound
            self.response.downloadable_as = 'katalog.csv'
            return catalog_file

    def set_content_type(self, resp, **kwargs):
        return settings.EXPORT_FORMAT_TO_MIMETYPE['csv']
