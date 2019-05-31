# -*- coding: utf-8 -*-
import json

import falcon
from django.template import loader
from elasticsearch import TransportError, RequestError
from elasticsearch_dsl import DateHistogramFacet, TermsFacet
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import get_connection

from mcod import settings
from mcod.core.api.openapi.specs import get_spec
from mcod.core.api.search.facets import NestedFacet
from mcod.core.api.versions import DOC_VERSIONS
from mcod.core.api.views import BaseView
from mcod.core.versioning import versioned
from mcod.datasets import serializers as dat_responses
from mcod.datasets import views as dat_views
from mcod.lib.encoders import DateTimeToISOEncoder
from mcod.lib.handlers import BaseHandler
from mcod.organizations.serializers import InstitutionApiResponse
from mcod.organizations import views as org_views
from mcod.resources import serializers as res_responses
from mcod.resources import views as res_views
from mcod.tools.depricated.schemas import StatsSchema
from mcod.tools.depricated.serializers import StatsMeta, StatsSerializer

indicies = [
    "articles",
    "applications",
    "institutions",
    "datasets",
    "resources",
]

connection = get_connection()


class StatsView(BaseView):

    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(BaseHandler):
        deserializer_schema = StatsSchema()
        serializer_schema = StatsSerializer(many=False)
        meta_serializer = StatsMeta()

        def _data(self, request, cleaned, *args, explain=None, **kwargs):
            search = Search(using=connection, index=indicies, extra={'size': 0})
            search.aggs.bucket('documents_by_type',
                               TermsFacet(field='_type').get_aggregation()) \
                .bucket('by_month',
                        DateHistogramFacet(field='created', interval='month', min_doc_count=0).get_aggregation())
            search.aggs.bucket('datasets_by_institution',
                               NestedFacet('institution',
                                           TermsFacet(field='institution.id')).get_aggregation())

            search.aggs.bucket('datasets_by_category',
                               NestedFacet('category',
                                           TermsFacet(field='category.id', min_doc_count=1, size=50)).get_aggregation())
            search.aggs.bucket('datasets_by_tags', TermsFacet(field='tags').get_aggregation())
            search.aggs.bucket('datasets_by_formats', TermsFacet(field='formats').get_aggregation())
            search.aggs.bucket('datasets_by_openness_scores', TermsFacet(field='openness_scores').get_aggregation())
            if explain == '1':
                return search.to_dict()
            try:
                return search.execute()
            except TransportError as err:
                raise falcon.HTTPBadRequest(description=err.info['error']['reason'])


class ClusterHealthView(object):
    def on_get(self, request, response, *args, **kwargs):
        response.body = json.dumps(connection.cluster.health())
        response.status = falcon.HTTP_200


class ClusterStateView(object):
    def on_get(self, request, response, *args, **kwargs):
        response.body = json.dumps(connection.cluster.state())
        response.status = falcon.HTTP_200


class ClusterAllocationView(object):
    def on_get(self, request, response, *args, **kwargs):
        try:
            result = connection.cluster.allocation_explain()
        except RequestError:
            result = {}
        response.body = json.dumps(result)
        response.status = falcon.HTTP_200


class SwaggerView(object):
    def on_get(self, request, response, *args, **kwargs):
        template = loader.get_template('swagger_ui/index.html')
        versions = sorted(DOC_VERSIONS, reverse=True)
        context = {
            'spec_url': '{}/spec/{}'.format(settings.API_URL, str(versions[0])),
            'spec_urls': [
                {'url': '{}/spec/{}'.format(settings.API_URL, str(version)),
                 'name': 'DANE.GOV.PL API v{}'.format(str(version))
                 } for version in versions
            ],
            'custom_css': 'custom.css'
        }

        response.status = falcon.HTTP_200
        response.content_type = 'text/html'
        response.body = template.render(context)


class OpenApiSpec(object):
    def on_get(self, req, resp, version=None, *args, **kwargs):
        if version and version not in DOC_VERSIONS:
            raise falcon.HTTPBadRequest(description='Invalid version')
        spec = get_spec(version=version)

        spec.components.schema('Institutions', schema=InstitutionApiResponse, many=True)
        spec.components.schema('Institution', schema=InstitutionApiResponse, many=False)
        spec.components.schema('Datasets', schema=dat_responses.DatasetApiResponse, many=True)
        spec.components.schema('Dataset', schema=dat_responses.DatasetApiResponse, many=False)
        spec.components.schema('Resources', schema=res_responses.ResourceApiResponse, many=True)
        spec.components.schema('Resource', schema=res_responses.ResourceApiResponse, many=False)
        spec.components.schema('ResourceTable', schema=res_responses.TableApiResponse, many=True)
        spec.components.schema('ResourceTableRow', schema=res_responses.TableApiResponse, many=False)

        spec.path(resource=org_views.InstitutionSearchView)
        spec.path(resource=org_views.InstitutionApiView)
        spec.path(resource=org_views.InstitutionDatasetSearchApiView)
        spec.path(resource=dat_views.DatasetSearchView)
        spec.path(resource=dat_views.DatasetApiView)
        spec.path(resource=dat_views.DatasetResourceSearchApiView)
        spec.path(resource=res_views.ResourcesView)
        spec.path(resource=res_views.ResourceView)
        spec.path(resource=res_views.ResourceTableView)
        spec.path(resource=res_views.ResourceTableRowView)

        resp.body = json.dumps(spec.to_dict(), cls=DateTimeToISOEncoder)
        resp.status = falcon.HTTP_200
