# -*- coding: utf-8 -*-
import json

import falcon
from django.template import loader
from elasticsearch import RequestError
from elasticsearch_dsl.connections import get_connection

from mcod import settings
from mcod.applications import views as app_views
from mcod.applications.serializers import ApplicationApiResponse
from mcod.api import app_cache as cache
from mcod.articles import views as art_views
from mcod.articles.serializers import ArticleApiResponse
from mcod.core.api.openapi.specs import get_spec
from mcod.core.api.versions import DOC_VERSIONS
from mcod.datasets import serializers as dat_responses
from mcod.datasets import views as dat_views
from mcod.histories.api import views as his_views
from mcod.histories.serializers import HistoryApiResponse
from mcod.lib.encoders import DateTimeToISOEncoder
from mcod.organizations.serializers import InstitutionApiResponse
from mcod.organizations import views as org_views
from mcod.resources import serializers as res_responses
from mcod.resources import views as res_views
from mcod.search import views as search_views
from mcod.search.serializers import CommonObjectResponse


connection = get_connection()


class ClusterHealthView(object):
    def on_get(self, request, response, *args, **kwargs):
        response.text = json.dumps(connection.cluster.health())
        response.status = falcon.HTTP_200


class ClusterStateView(object):
    def on_get(self, request, response, *args, **kwargs):
        response.text = json.dumps(connection.cluster.state())
        response.status = falcon.HTTP_200


class ClusterAllocationView(object):
    def on_get(self, request, response, *args, **kwargs):
        try:
            result = connection.cluster.allocation_explain()
        except RequestError:
            result = {}
        response.text = json.dumps(result)
        response.status = falcon.HTTP_200


class SwaggerView(object):
    def on_get(self, request, response, *args, **kwargs):
        template = loader.get_template('swagger_ui/index.html')
        versions = sorted(DOC_VERSIONS, reverse=True)

        rdf_spec_name = 'DANE.GOV.PL RDF API'
        default_spec_name = f'DANE.GOV.PL API v{versions[0]}'
        spec_name = request.params.get('urls.primaryName', default_spec_name)

        api_spec_urls = [
            {
                'url': f'{settings.API_URL}/spec/{version}',
                'name': f'DANE.GOV.PL API v{version}',
            }
            for version in versions
        ]
        rdf_api_spec_url = {
            'url': f'{settings.API_URL}/catalog/spec',
            'name': rdf_spec_name,
        }

        if spec_name == rdf_spec_name:
            spec_urls = [rdf_api_spec_url, *api_spec_urls]
        else:
            spec_urls = [*api_spec_urls, rdf_api_spec_url]

        context = {
            'spec_urls': spec_urls,
            'custom_css': 'custom.css'
        }

        response.status = falcon.HTTP_200
        response.content_type = 'text/html'
        response.text = template.render(context)


class OpenApiSpec(object):
    def on_get(self, req, resp, version=None, *args, **kwargs):
        if version and version not in DOC_VERSIONS:
            raise falcon.HTTPBadRequest(description='Invalid version')
        spec = get_spec(version=version)

        spec.components.schema('Applications', schema=ApplicationApiResponse, many=True)
        spec.components.schema('Application', schema=ApplicationApiResponse, many=False)
        spec.components.schema('Articles', schema=ArticleApiResponse, many=True)
        spec.components.schema('Article', schema=ArticleApiResponse, many=False)
        spec.components.schema('Institutions', schema=InstitutionApiResponse, many=True)
        spec.components.schema('Institution', schema=InstitutionApiResponse, many=False)
        spec.components.schema('Datasets', schema=dat_responses.DatasetApiResponse, many=True)
        spec.components.schema('Dataset', schema=dat_responses.DatasetApiResponse, many=False)
        spec.components.schema('Resources', schema=res_responses.ResourceApiResponse, many=True)
        spec.components.schema('Resource', schema=res_responses.ResourceApiResponse, many=False)
        spec.components.schema('Charts', schema=res_responses.ChartApiResponse, many=True)
        spec.components.schema('Chart', schema=res_responses.ChartApiResponse, many=False)
        spec.components.schema('ResourceTable', schema=res_responses.TableApiResponse, many=True)
        spec.components.schema('ResourceTableRow', schema=res_responses.TableApiResponse, many=False)
        spec.components.schema('Search', schema=CommonObjectResponse, many=True)
        spec.components.schema('Histories', schema=HistoryApiResponse, many=True)
        spec.components.schema('History', schema=HistoryApiResponse, many=False)

        spec.path(resource=app_views.ApplicationSearchApiView)
        spec.path(resource=app_views.ApplicationApiView)
        spec.path(resource=app_views.ApplicationDatasetsView)
        spec.path(resource=art_views.ArticlesView)
        spec.path(resource=art_views.ArticleView)
        spec.path(resource=art_views.ArticleDatasetsView)
        spec.path(resource=org_views.InstitutionSearchView)
        spec.path(resource=org_views.InstitutionApiView)
        spec.path(resource=org_views.InstitutionDatasetSearchApiView)
        spec.path(resource=dat_views.DatasetSearchView)
        spec.path(resource=dat_views.DatasetApiView)
        spec.path(resource=dat_views.DatasetResourceSearchApiView)
        spec.path(resource=res_views.ResourcesView)
        spec.path(resource=res_views.ResourceView)
        # spec.path(resource=res_views.ChartsView)
        # spec.path(resource=res_views.ChartView)
        spec.path(resource=res_views.ResourceTableView)
        spec.path(resource=res_views.ResourceTableRowView)
        spec.path(resource=search_views.SearchView)
        spec.path(resource=his_views.HistoriesView)
        spec.path(resource=his_views.HistoryView)

        resp.text = json.dumps(spec.to_dict(), cls=DateTimeToISOEncoder)
        resp.status = falcon.HTTP_200


class CatalogOpenApiSpec(object):
    @cache.cached(timeout=60 * 60 * 24)
    def on_get(self, req, resp, version=None, *args, **kwargs):
        with open(settings.SPEC_DIR.path('rdf_api_desc.html'), 'r') as file:
            description = file.read()
        with open(settings.SPEC_DIR.path('rdf_api_spec.json'), 'rb') as file:
            spec = json.load(file)
        spec['info']['description'] = description
        resp.media = spec
        resp.status = falcon.HTTP_200
