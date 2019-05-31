import falcon
from django.apps import apps

from mcod.applications.depricated.schemas import ApplicationsList
from mcod.applications.depricated.serializers import ApplicationsSerializer, ApplicationsMeta
from mcod.applications.documents import ApplicationsDoc
from mcod.articles.depricated.schemas import ArticlesList
from mcod.articles.depricated.serializers import ArticlesSerializer, ArticlesMeta
from mcod.articles.documents import ArticleDoc
from mcod.core.api.hooks import login_required
from mcod.core.api.views import BaseView
from mcod.core.versioning import versioned
from mcod.datasets.depricated.schemas import DatasetsList
from mcod.datasets.depricated.serializers import DatasetSerializer, DatasetsMeta
from mcod.datasets.documents import DatasetsDoc
from mcod.following.handlers import CreateFollowingHandler, DeleteFollowingHandler, FollowedListHandler


class FollowApplication(BaseView):
    @falcon.before(login_required)
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @versioned
    def on_delete(self, request, response, *args, **kwargs):
        self.handle(request, response, self.DELETE_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_delete.version('1.0')
    def on_delete(self, request, response, *args, **kwargs):
        self.handle(request, response, self.DELETE_1_0, *args, **kwargs)

    class POST_1_0(CreateFollowingHandler):
        database_model = apps.get_model('users', 'UserFollowingApplication')
        resource_model = apps.get_model('applications', 'Application')
        resource_name = 'application'
        serializer_schema = ApplicationsSerializer(many=False)

    class DELETE_1_0(DeleteFollowingHandler):
        database_model = apps.get_model('users', 'UserFollowingApplication')
        resource_model = apps.get_model('applications', 'Application')
        resource_name = 'application'
        serializer_schema = ApplicationsSerializer(many=False)


class FollowDataset(BaseView):
    @falcon.before(login_required)
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @versioned
    def on_delete(self, request, response, *args, **kwargs):
        self.handle(request, response, self.DELETE_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_delete.version('1.0')
    def on_delete(self, request, response, *args, **kwargs):
        self.handle(request, response, self.DELETE_1_0, *args, **kwargs)

    class POST_1_0(CreateFollowingHandler):
        database_model = apps.get_model('users', 'UserFollowingDataset')
        resource_model = apps.get_model('datasets', 'Dataset')
        resource_name = 'dataset'
        serializer_schema = DatasetSerializer(many=False)

    class DELETE_1_0(DeleteFollowingHandler):
        database_model = apps.get_model('users', 'UserFollowingDataset')
        resource_model = apps.get_model('datasets', 'Dataset')
        resource_name = 'dataset'
        serializer_schema = DatasetSerializer(many=False)


class FollowArticle(BaseView):
    @falcon.before(login_required)
    @versioned
    def on_post(self, request, response, *args, **kwargs):
        self.handle_post(request, response, self.POST_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_post.version('1.0')
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @versioned
    def on_delete(self, request, response, *args, **kwargs):
        self.handle(request, response, self.DELETE_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_delete.version('1.0')
    def on_delete(self, request, response, *args, **kwargs):
        self.handle(request, response, self.DELETE_1_0, *args, **kwargs)

    class POST_1_0(CreateFollowingHandler):
        database_model = apps.get_model('users', 'UserFollowingArticle')
        resource_model = apps.get_model('articles', 'Article')
        resource_name = 'article'
        serializer_schema = ArticlesSerializer(many=False)

    class DELETE_1_0(DeleteFollowingHandler):
        database_model = apps.get_model('users', 'UserFollowingArticle')
        resource_model = apps.get_model('articles', 'Article')
        resource_name = 'article'
        serializer_schema = ArticlesSerializer(many=False)


class ListOfFollowedApplications(BaseView):
    @falcon.before(login_required)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(FollowedListHandler):
        meta_serializer = ApplicationsMeta()
        deserializer_schema = ApplicationsList()
        serializer_schema = ApplicationsSerializer(many=True)
        search_document = ApplicationsDoc()


class ListOfFollowedArticles(BaseView):
    @falcon.before(login_required)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(FollowedListHandler):
        meta_serializer = ArticlesMeta()
        deserializer_schema = ArticlesList()
        serializer_schema = ArticlesSerializer(many=True)
        search_document = ArticleDoc()


class ListOfFollowedDatasets(BaseView):
    @falcon.before(login_required)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @falcon.before(login_required)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(FollowedListHandler):
        meta_serializer = DatasetsMeta()
        deserializer_schema = DatasetsList()
        serializer_schema = DatasetSerializer(many=True, include_data=('institution',))
        search_document = DatasetsDoc()
