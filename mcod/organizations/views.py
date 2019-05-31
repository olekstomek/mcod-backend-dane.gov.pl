# -*- coding: utf-8 -*-
from functools import partial

import falcon
from dal import autocomplete
from django.apps import apps
from elasticsearch_dsl import Q

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
from mcod.lib.handlers import SearchHandler, RetrieveOneHandler
from mcod.organizations.depricated.schemas import InstitutionsList
from mcod.organizations.depricated.serializers import InstitutionsSerializer, InstitutionsMeta
from mcod.organizations.deserializers import InstitutionApiRequest, InstitutionApiSearchRequest
from mcod.organizations.documents import InstitutionDoc
from mcod.organizations.models import Organization
from mcod.organizations.serializers import InstitutionApiResponse


class InstitutionSearchView(BaseView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/institutions/institutions_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(InstitutionApiSearchRequest, many=False)
        serializer_schema = partial(InstitutionApiResponse, many=True)
        search_document = InstitutionDoc()

        def _queryset_extra(self, queryset, **kwargs):
            return queryset.filter('term', status=Organization.STATUS.published)

    class GET_1_0(SearchHandler):
        meta_serializer = InstitutionsMeta()
        deserializer_schema = InstitutionsList()
        serializer_schema = InstitutionsSerializer(many=True)
        search_document = InstitutionDoc()


class InstitutionApiView(BaseView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/institutions/institution_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        deserializer_schema = partial(InstitutionApiRequest, many=False)
        database_model = apps.get_model('organizations', 'Organization')
        serializer_schema = partial(InstitutionApiResponse, many=False)

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_instance', None)
            if not instance:
                model = self.database_model
                try:
                    self._cached_instance = model.objects.get(pk=id, status='published')
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance

    class GET_1_0(RetrieveOneHandler):
        database_model = apps.get_model('organizations', 'Organization')
        serializer_schema = InstitutionsSerializer(many=False, include_data=('datasets',))

        def _clean(self, request, id, *args, **kwargs):
            model = self.database_model
            try:
                return model.objects.get(pk=id, status="published")
            except model.DoesNotExist:
                raise falcon.HTTPNotFound


class InstitutionDatasetSearchApiView(BaseView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/institutions/institution_datasets_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(DatasetApiSearchRequest, many=False)
        serializer_schema = partial(DatasetApiResponse, many=True)
        search_document = DatasetsDoc()

        def _queryset_extra(self, queryset, id=None, **kwargs):
            if id:
                queryset = queryset.query("nested", path="institution",
                                          query=Q("term", **{'institution.id': id}))
            return queryset.filter('term', status='published')

    class GET_1_0(FollowingSearchHandler):
        meta_serializer = DatasetsMeta()
        deserializer_schema = DatasetsList()
        serializer_schema = DatasetSerializer(many=True)
        search_document = DatasetsDoc()

        def _queryset(self, cleaned, *args, **kwargs):
            qs = super()._queryset(cleaned, *args, **kwargs)
            if 'id' in kwargs:
                qs = qs.query("nested", path="institution",
                              query=Q("term", **{'institution.id': kwargs['id']}))
            return qs


class InstitutionAutocompleteAdminView(autocomplete.Select2QuerySetView):
    def get_queryset(self):

        user = self.request.user
        # Don't forget to filter out results depending on the visitor !
        if not user.is_authenticated:
            return Organization.objects.none()

        if user.is_superuser:
            qs = Organization.objects.all()
        else:
            qs = Organization.objects.filter(id__in=user.organizations.all())

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return qs
