# -*- coding: utf-8 -*-

from collections import namedtuple
from functools import partial
from uuid import uuid4

import falcon
from django.apps import apps
from elasticsearch_dsl import Q

from mcod.applications.depricated.schemas import ApplicationsList, ApplicationSuggestion
from mcod.applications.depricated.serializers import ApplicationsSerializer, ApplicationsMeta
from mcod.applications.deserializers import ApplicationApiRequest, ApplicationApiSearchRequest, CreateSubmissionRequest
from mcod.applications.documents import ApplicationsDoc
from mcod.applications.serializers import ApplicationApiResponse, SubmissionApiResponse
from mcod.applications.tasks import send_application_proposal
from mcod.core.api.handlers import CreateOneHdlr
from mcod.core.api.handlers import SearchHdlr, RetrieveOneHdlr
from mcod.core.api.hooks import login_optional
from mcod.core.api.views import BaseView
from mcod.core.versioning import versioned
from mcod.datasets.depricated.schemas import DatasetsList
from mcod.datasets.depricated.serializers import DatasetSerializer, DatasetsMeta
from mcod.datasets.deserializers import DatasetApiSearchRequest
from mcod.datasets.documents import DatasetsDoc
from mcod.datasets.serializers import DatasetApiResponse
from mcod.following.handlers import FollowingSearchHandler
from mcod.following.handlers import RetrieveOneFollowHandler
from mcod.lib.handlers import (
    CreateHandler)
from mcod.lib.handlers import SearchHandler


class ApplicationSearchApiView(BaseView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(ApplicationApiSearchRequest, many=False)
        serializer_schema = partial(ApplicationApiResponse, many=True)
        search_document = ApplicationsDoc()

        def _queryset_extra(self, queryset, **kwargs):
            return queryset.filter('term', status='published')

    class GET_1_0(FollowingSearchHandler):
        meta_serializer = ApplicationsMeta()
        deserializer_schema = ApplicationsList()
        serializer_schema = ApplicationsSerializer(many=True)
        search_document = ApplicationsDoc()


class ApplicationApiView(BaseView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(RetrieveOneFollowHandler):
        database_model = apps.get_model('applications', 'Application')
        serializer_schema = ApplicationsSerializer(many=False)

    class GET(RetrieveOneHdlr):
        deserializer_schema = partial(ApplicationApiRequest, many=False)
        database_model = apps.get_model('applications', 'Application')
        serializer_schema = partial(ApplicationApiResponse, many=False)

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_instance', None)
            if not instance:
                model = self.database_model
                try:
                    self._cached_instance = model.objects.get(pk=id, status='published')
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance


class ApplicationDatasetsView(BaseView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(SearchHandler):
        meta_serializer = DatasetsMeta()
        deserializer_schema = DatasetsList()
        serializer_schema = DatasetSerializer(many=True, include_data=('institution',))
        search_document = DatasetsDoc()

        def _queryset(self, cleaned, *args, **kwargs):
            qs = super()._queryset(cleaned, *args, **kwargs)
            if 'id' in kwargs:
                qs = qs.query("nested", path="applications",
                              query=Q("term", **{'applications.id': kwargs['id']}))
            return qs

    class GET(SearchHdlr):
        deserializer_schema = partial(DatasetApiSearchRequest, many=False)
        serializer_schema = partial(DatasetApiResponse, many=True)
        search_document = DatasetsDoc()

        def _queryset_extra(self, queryset, id=None, **kwargs):
            if id:
                queryset = queryset.query("nested", path="applications",
                                          query=Q("term", **{'applications.id': id}))
            return queryset.filter('term', status='published')


class ApplicationSubmitView(BaseView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)

    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    class POST_1_0(CreateHandler):
        databse_model = apps.get_model('applications', 'Application')
        deserializer_schema = ApplicationSuggestion()

        def _data(self, request, cleaned, *args, **kwargs):
            send_application_proposal.delay(cleaned)
            return cleaned

        def _serialize(self, data, meta, links=None, *args, **kwargs):
            return {}

    class POST(CreateOneHdlr):
        databse_model = apps.get_model('applications', 'Application')
        deserializer_schema = partial(CreateSubmissionRequest)
        serializer_schema = partial(SubmissionApiResponse, many=False)

        def clean(self, *args, **kwargs):
            cleaned = super().clean(*args, **kwargs)
            return cleaned

        def _get_data(self, cleaned, *args, **kwargs):
            _data = cleaned['data']['attributes']
            send_application_proposal.s(dict(_data)).apply_async(countdown=1)
            fields, values = [], []
            for field, val in _data.items():
                fields.append(field)
                values.append(val)
            fields.append('id')
            values.append(str(uuid4()))
            result = namedtuple('Submission', fields)(*values)
            return result
