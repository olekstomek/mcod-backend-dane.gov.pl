import falcon
from functools import partial
from elasticsearch_dsl import Q

from mcod.core.api.handlers import SearchHdlr
from mcod.core.api.hooks import login_required
from mcod.core.api.views import JsonAPIView
from mcod.core.versioning import versioned
from mcod.lib.handlers import SearchHandler
from mcod.lib.serializers import SearchMeta
from mcod.searchhistories.depricated.schemas import SearchHistoriesList
from mcod.searchhistories.depricated.serializers import SearchHistorySerializer
from mcod.searchhistories.deserializers import SearchHistoryApiSearchRequest
from mcod.searchhistories.documents import SearchHistoriesDoc
from mcod.searchhistories.serializers import SearchHistoryApiResponse


class SearchHistoriesView(JsonAPIView):
    @falcon.before(login_required)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_required)
    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = partial(SearchHistoryApiSearchRequest, many=False)
        serializer_schema = partial(SearchHistoryApiResponse, many=True)
        search_document = SearchHistoriesDoc()

        def _queryset_extra(self, queryset, *args, **kwargs):
            qs = super()._queryset_extra(queryset, *args, **kwargs)
            return qs.filter('nested', path='user', query=Q('match', **{'user.id': self.request.user.id}))

    class GET_1_0(SearchHandler):
        meta_serializer = SearchMeta()
        deserializer_schema = SearchHistoriesList()
        serializer_schema = SearchHistorySerializer(many=True)
        search_document = SearchHistoriesDoc()

        def _clean(self, request, *args, locations=None, **kwargs):
            self.req = request
            return super()._clean(request, *args, locations, **kwargs)

        def _queryset(self, cleaned, *args, **kwargs):
            qs = super()._queryset(cleaned, *args, **kwargs)

            return qs.filter(
                'nested',
                path='user',
                query=Q('match', **{'user.id': self.req.user.id}),
            )
