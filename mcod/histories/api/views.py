from functools import partial

import falcon
from django.apps import apps

from mcod.core.api.handlers import RetrieveOneHdlr, SearchHdlr
from mcod.core.api.views import JsonAPIView
from mcod.core.versioning import versioned
from mcod.histories.deserializers import HistoryApiRequest, HistoryApiSearchRequest, LogEntryApiSearchRequest
from mcod.histories.documents import HistoriesDoc, LogEntryDoc
from mcod.histories.serializers import HistoryApiResponse, LogEntryApiResponse
from mcod.unleash import is_enabled


class HistoriesView(JsonAPIView):
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        """
        ---
        doc_template: docs/histories/histories_view.yml
        """
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(SearchHdlr):
        new_history = is_enabled('S30_new_history.be')
        if new_history:
            deserializer_schema = LogEntryApiSearchRequest
            search_document = LogEntryDoc()
            serializer_schema = partial(LogEntryApiResponse, many=True)
        else:
            deserializer_schema = HistoryApiSearchRequest
            search_document = HistoriesDoc()
            serializer_schema = partial(HistoryApiResponse, many=True)

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
        new_history = is_enabled('S30_new_history.be')
        if new_history:
            database_model = apps.get_model('histories', 'LogEntry')
            serializer_schema = LogEntryApiResponse
        else:
            database_model = apps.get_model('histories', 'History')
            serializer_schema = HistoryApiResponse
        deserializer_schema = HistoryApiRequest

        def _get_instance(self, id, *args, **kwargs):
            instance = getattr(self, '_cached_instance', None)
            if not instance:
                query = {'content_type__model': 'user'} if self.new_history else {'table_name': 'user'}
                try:
                    self._cached_instance = self.database_model.objects.exclude(**query).get(pk=id)
                except self.database_model.DoesNotExist:
                    raise falcon.HTTPNotFound
            return self._cached_instance
