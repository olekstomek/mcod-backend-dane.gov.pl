from functools import partial

import falcon
from django.apps import apps
from elasticsearch_dsl.query import Q

from mcod.articles.deserializers import ArticleApiRequest, ArticleApiSearchRequest
from mcod.articles.documents import ArticleDocument
from mcod.articles.serializers import ArticleApiResponse
from mcod.core.api.handlers import RetrieveOneHdlr, SearchHdlr
from mcod.core.api.hooks import login_optional
from mcod.core.api.views import JsonAPIView
from mcod.core.versioning import versioned
from mcod.datasets.deserializers import DatasetApiSearchRequest
from mcod.datasets.documents import DatasetDocument
from mcod.datasets.serializers import DatasetApiResponse


class ArticlesView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/articles/articles_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(ArticleApiSearchRequest, many=False)
        serializer_schema = partial(ArticleApiResponse, many=True)
        search_document = ArticleDocument()


class ArticleView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/articles/article_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        deserializer_schema = partial(ArticleApiRequest, many=False)
        database_model = apps.get_model('articles', 'Article')
        serializer_schema = partial(ArticleApiResponse, many=False)

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_instance', None)
            if not instance:
                model = self.database_model
                try:
                    usr = getattr(self.request, 'user', None)
                    if usr and usr.is_superuser:
                        self._cached_instance = model.objects.get(pk=id, status__in=["published", 'draft'])
                    else:
                        self._cached_instance = model.objects.get(pk=id, status='published')
                except model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance


class ArticleDatasetsView(JsonAPIView):
    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/articles/article_datasets_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_optional)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(DatasetApiSearchRequest, many=False)
        serializer_schema = partial(DatasetApiResponse, many=True)
        search_document = DatasetDocument()
        include_default = ['institution']

        def _queryset_extra(self, queryset, id=None, **kwargs):
            if id:
                queryset = queryset.query("nested", path="articles",
                                          query=Q("term", **{'articles.id': id}))
            return queryset.filter('term', status='published')
