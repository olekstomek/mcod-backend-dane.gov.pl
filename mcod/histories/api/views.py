from django.apps import apps

from mcod.core.api.views import BaseView
from mcod.core.versioning import versioned
from mcod.histories.depricated.schemas import HistoriesList
from mcod.histories.depricated.serializers import HistorySerializer
from mcod.histories.documents import HistoriesDoc
from mcod.lib.handlers import SearchHandler, RetrieveOneHandler
from mcod.lib.serializers import SearchMeta


class HistoriesView(BaseView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(SearchHandler):
        meta_serializer = SearchMeta()
        deserializer_schema = HistoriesList()
        serializer_schema = HistorySerializer(many=True)
        search_document = HistoriesDoc()

        def _queryset(self, cleaned, *args, **kwargs):
            qs = super()._queryset(cleaned, *args, **kwargs)
            return qs.exclude('terms', change_user_id=[1])


class HistoryView(BaseView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    @on_get.version('1.0')
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET_1_0, *args, **kwargs)

    class GET_1_0(RetrieveOneHandler):
        database_model = apps.get_model('histories', 'History')
        serializer_schema = HistorySerializer(many=False)
