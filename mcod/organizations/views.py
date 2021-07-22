# -*- coding: utf-8 -*-
from functools import partial

import falcon
from dal import autocomplete
from django.apps import apps
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from elasticsearch_dsl import Q

from mcod.core.api.handlers import SearchHdlr, RetrieveOneHdlr, SubscriptionSearchHdlr
from mcod.core.api.hooks import login_optional
from mcod.core.api.views import JsonAPIView
from mcod.core.versioning import versioned
from mcod.datasets.deserializers import DatasetApiSearchRequest
from mcod.datasets.documents import DatasetDocumentActive
from mcod.datasets.serializers import DatasetApiResponse
from mcod.organizations.deserializers import InstitutionApiRequest, InstitutionApiSearchRequest
from mcod.organizations.documents import InstitutionDocumentActive
from mcod.organizations.models import Organization
from mcod.organizations.serializers import InstitutionApiResponse


class InstitutionSearchView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/institutions/institutions_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SubscriptionSearchHdlr):
        deserializer_schema = partial(InstitutionApiSearchRequest, many=False)
        serializer_schema = partial(InstitutionApiResponse, many=True)
        search_document = InstitutionDocumentActive()


class InstitutionApiView(JsonAPIView):
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
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        deserializer_schema = partial(InstitutionApiRequest, many=False)
        database_model = apps.get_model('organizations', 'Organization')
        serializer_schema = partial(InstitutionApiResponse, many=False)
        include_default = ['dataset']


class InstitutionDatasetSearchApiView(JsonAPIView):
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
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(DatasetApiSearchRequest, many=False)
        serializer_schema = partial(DatasetApiResponse, many=True)
        search_document = DatasetDocumentActive()

        def _queryset_extra(self, queryset, id=None, **kwargs):
            if id:
                queryset = queryset.query("nested", path="institution",
                                          query=Q("term", **{'institution.id': id}))
            return queryset.filter('term', status='published')


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


class InstitutionTypeAdminView(PermissionRequiredMixin, View):
    http_method_names = ['get']

    def has_permission(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        organization_id = request.GET.get('organization_id')
        organization = get_object_or_404(Organization, id=organization_id)
        return JsonResponse({'institution_type': organization.institution_type})
