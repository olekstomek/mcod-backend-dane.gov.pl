# -*- coding: utf-8 -*-
from collections import namedtuple
from functools import partial
from uuid import uuid4

import falcon
from dal import autocomplete
from django.apps import apps
from elasticsearch_dsl import Q

from mcod.core.api.handlers import SearchHdlr, RetrieveOneHdlr, CreateOneHdlr
from mcod.core.api.hooks import login_optional
from mcod.core.api.views import BaseView
from mcod.core.versioning import versioned
from mcod.datasets.depricated.schemas import DatasetsList
from mcod.datasets.depricated.serializers import DatasetSerializer, DatasetsMeta
from mcod.datasets.deserializers import DatasetApiRequest, DatasetApiSearchRequest, CreateCommentRequest
from mcod.datasets.documents import DatasetsDoc
from mcod.datasets.models import Dataset
from mcod.datasets.serializers import DatasetApiResponse, CommentApiResponse
from mcod.datasets.tasks import send_dataset_comment
from mcod.following.handlers import RetrieveOneFollowHandler, FollowingSearchHandler
from mcod.lib.handlers import SearchHandler
from mcod.resources.depricated.schemas import ResourcesList
from mcod.resources.depricated.serializers import ResourceSerializer, ResourcesMeta
from mcod.resources.deserializers import ResourceApiSearchRequest
from mcod.resources.documents import ResourceDoc
from mcod.resources.serializers import ResourceApiResponse


class DatasetSearchView(BaseView):
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
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(FollowingSearchHandler):
        meta_serializer = DatasetsMeta()
        deserializer_schema = DatasetsList()
        serializer_schema = DatasetSerializer(many=True, include_data=('institution',))
        search_document = DatasetsDoc()

        def _queryset(self, cleaned, *args, **kwargs):
            qs = super()._queryset(cleaned, *args, **kwargs)
            return qs.filter('match', status=Dataset.STATUS.published)

    class GET(SearchHdlr):
        deserializer_schema = partial(DatasetApiSearchRequest, many=False)
        serializer_schema = partial(DatasetApiResponse, many=True)
        search_document = DatasetsDoc()

        def _queryset_extra(self, queryset, **kwargs):
            return queryset.filter('match', status=Dataset.STATUS.published)


class DatasetApiView(BaseView):
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
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        deserializer_schema = partial(DatasetApiRequest)
        database_model = apps.get_model('datasets', 'Dataset')
        serializer_schema = partial(DatasetApiResponse, many=False)

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_instance', None)
            if not instance:
                model = self.database_model
                try:
                    self._cached_instance = model.objects.get(pk=id, status=Dataset.STATUS.published)
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance

    class GET_1_0(RetrieveOneFollowHandler):
        database_model = apps.get_model('datasets', 'Dataset')
        serializer_schema = DatasetSerializer(many=False, include_data=('institution', 'resources'))

        def _clean(self, request, id, *args, **kwargs):
            if hasattr(self, 'resource_clean'):
                obj = self.resource_clean(request, id, *args, **kwargs)
            else:
                obj = super()._clean(request, id, *args, **kwargs)

            res = {
                'resource': obj,
                'follower': request.user
            }
            return res

        def resource_clean(self, request, id, *args, **kwargs):
            model = self.database_model
            try:
                return model.objects.get(pk=id, status=Dataset.STATUS.published)
            except model.DoesNotExist:
                raise falcon.HTTPNotFound


class DatasetResourceSearchApiView(BaseView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/datasets/dataset_resources_view.yml

        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(ResourceApiSearchRequest, many=False)
        serializer_schema = partial(ResourceApiResponse, many=True)
        search_document = ResourceDoc()

        def _queryset_extra(self, queryset, id=None, **kwargs):
            if id:
                queryset = queryset.query("nested", path="dataset",
                                          query=Q("term", **{'dataset.id': id}))
            return queryset.filter('term', status=Dataset.STATUS.published)

    class GET_1_0(SearchHandler):
        meta_serializer = ResourcesMeta()
        deserializer_schema = ResourcesList()
        serializer_schema = ResourceSerializer(many=True)
        search_document = ResourceDoc()

        def _queryset(self, cleaned, *args, **kwargs):
            qs = super()._queryset(cleaned, *args, **kwargs)
            if 'id' in kwargs:
                qs = qs.query(
                    "nested", path="dataset",
                    query=Q("term", **{'dataset.id': kwargs['id']})
                ).filter('term', status=Dataset.STATUS.published)
            return qs


class DatasetCommentSearchApiView(BaseView):
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        deserializer_schema = partial(CreateCommentRequest)
        serializer_schema = partial(CommentApiResponse, many=False)
        database_model = apps.get_model('datasets', 'Dataset')

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
            send_dataset_comment.s(id, attrs['comment']).apply_async(countdown=1)
            result = namedtuple('Comment', ['id', 'comment', 'dataset'])(
                str(uuid4()),
                attrs['comment'],
                self._get_resource(id, *args, **kwargs)
            )
            return result


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
