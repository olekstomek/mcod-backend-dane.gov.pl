from functools import partial

import falcon
from django.apps import apps

from mcod.core.api.handlers import RetrieveOneHdlr, SearchHdlr
from mcod.core.api.views import JsonAPIView
from mcod.core.versioning import versioned
from mcod.histories.deserializers import HistoryApiRequest, HistoryApiSearchRequest
from mcod.histories.documents import HistoriesDoc
from mcod.histories.serializers import HistoryApiResponse


class HistoriesView(JsonAPIView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/histories/histories_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SearchHdlr):
        deserializer_schema = HistoryApiSearchRequest
        serializer_schema = partial(HistoryApiResponse, many=True)
        search_document = HistoriesDoc()

        def _queryset_extra(self, queryset, **kwargs):
            return queryset.exclude('terms', change_user_id=[1])


class HistoryView(JsonAPIView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/histories/history_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        database_model = apps.get_model('histories', 'History')
        deserializer_schema = HistoryApiRequest
        serializer_schema = HistoryApiResponse

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_instance', None)
            if not instance:
                try:
                    self._cached_instance = self.database_model.objects.exclude(table_name='user').get(pk=id)
                except self.database_model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance
