# -*- coding: utf-8 -*-
import falcon
from django.apps import apps
from elasticsearch_dsl import Q

from mcod.articles.depricated.schemas import ArticlesList
from mcod.articles.depricated.serializers import ArticlesSerializer, ArticlesMeta
from mcod.articles.documents import ArticleDoc
from mcod.core.api.hooks import login_optional
from mcod.core.api.views import BaseView
from mcod.core.versioning import versioned
from mcod.datasets.depricated.schemas import DatasetsList
from mcod.datasets.depricated.serializers import DatasetSerializer, DatasetsMeta
from mcod.datasets.documents import DatasetsDoc
from mcod.following.handlers import RetrieveOneFollowHandler, FollowingSearchHandler
from mcod.lib.handlers import SearchHandler


class ArticlesView(BaseView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(FollowingSearchHandler):
        meta_serializer = ArticlesMeta()
        deserializer_schema = ArticlesList()
        serializer_schema = ArticlesSerializer(many=True)
        search_document = ArticleDoc()

        def _queryset(self, cleaned, *args, **kwargs):
            qs = super()._queryset(cleaned, *args, **kwargs)
            return qs.filter('match', status='published')


class ArticleView(BaseView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(RetrieveOneFollowHandler):
        database_model = apps.get_model('articles', 'Article')
        serializer_schema = ArticlesSerializer(many=False)

        def resource_clean(self, request, id, *args, **kwargs):
            model = self.database_model
            try:
                if request.user.is_superuser:
                    return model.objects.get(pk=id, status__in=["published", 'draft'])
                return model.objects.get(pk=id, status="published")
            except model.DoesNotExist:
                raise falcon.HTTPNotFound


class ArticleDatasetsView(BaseView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

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
                qs = qs.query("nested", path="articles",
                              query=Q("term", **{'articles.id': kwargs['id']}))
            return qs
