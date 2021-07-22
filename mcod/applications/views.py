# -*- coding: utf-8 -*-
from collections import namedtuple
from functools import partial
from uuid import uuid4

import falcon
from django.apps import apps
from elasticsearch_dsl import Q

from mcod.applications.deserializers import ApplicationApiRequest, ApplicationApiSearchRequest, CreateSubmissionRequest
from mcod.applications.documents import ApplicationDocumentActive
from mcod.applications.serializers import ApplicationApiResponse, SubmissionApiResponse
from mcod.applications.tasks import create_application_proposal_task, send_application_proposal
from mcod.core.api.handlers import CreateOneHdlr, SearchHdlr, RetrieveOneHdlr
from mcod.core.api.hooks import login_optional
from mcod.core.api.views import JsonAPIView
from mcod.core.versioning import versioned
from mcod.datasets.deserializers import DatasetApiSearchRequest
from mcod.datasets.documents import DatasetDocumentActive
from mcod.datasets.serializers import DatasetApiResponse


class ApplicationSearchApiView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/applications/applications_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(ApplicationApiSearchRequest, many=False)
        serializer_schema = partial(ApplicationApiResponse, many=True)
        search_document = ApplicationDocumentActive()


class ApplicationApiView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/applications/application_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        deserializer_schema = partial(ApplicationApiRequest, many=False)
        database_model = apps.get_model('applications', 'Application')
        serializer_schema = partial(ApplicationApiResponse, many=False)

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_instance', None)
            if not instance:
                model = self.database_model
                try:
                    user = getattr(self.request, 'user', None)
                    data = {'id': id, 'status': 'published'}
                    if user and user.is_superuser:
                        data = {'id': id, 'status__in': ['draft', 'published']}
                    self._cached_instance = model.objects.get(**data)
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance


class ApplicationDatasetsView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/applications/application_datasets_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(DatasetApiSearchRequest, many=False)
        serializer_schema = partial(DatasetApiResponse, many=True)
        search_document = DatasetDocumentActive()
        include_default = ['institution']

        def _queryset_extra(self, queryset, id=None, **kwargs):
            if id:
                queryset = queryset.query("nested", path="applications",
                                          query=Q("term", **{'applications.id': id}))
            return queryset.filter('term', status='published')


class ApplicationSubmitView(JsonAPIView):
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST, *args, **kwargs)

    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        database_model = apps.get_model('applications', 'Application')
        deserializer_schema = partial(CreateSubmissionRequest)
        serializer_schema = partial(SubmissionApiResponse, many=False)

        def _get_data(self, cleaned, *args, **kwargs):
            _data = cleaned['data']['attributes']
            _data.pop('is_personal_data_processing_accepted', None)
            _data.pop('is_terms_of_service_accepted', None)
            create_application_proposal_task.s(_data).apply_async()
            send_application_proposal.s(_data).apply_async(countdown=1)
            fields, values = [], []
            for field, val in _data.items():
                fields.append(field)
                values.append(val)
            fields.append('id')
            values.append(str(uuid4()))
            result = namedtuple('Submission', fields)(*values)
            return result
