from functools import partial

from django.apps import apps

from mcod.core.api.handlers import RetrieveManyHdlr
from mcod.datasets.deserializers import DatasetResourcesDownloadApiRequest
from mcod.resources.serializers import DatasetResourcesCSVSerializer


class DatasetResourcesMetadataViewHandler(RetrieveManyHdlr):
    deserializer_schema = DatasetResourcesDownloadApiRequest
    database_model = apps.get_model('resources', 'Resource')
    serializer_schema = partial(DatasetResourcesCSVSerializer, many=True)

    def _get_data(self, cleaned, *args, **kwargs):
        return self._get_queryset(cleaned, *args, **kwargs).with_metadata()

    def prepare_context(self, *args, **kwargs):
        super().prepare_context(*args, **kwargs)
        self.response.context.serializer_schema = self.serializer

    def serialize(self, *args, **kwargs):
        self.prepare_context(*args, **kwargs)
        self.response.downloadable_as = '{}.csv'.format(kwargs.get('id', 'katalog'))
        return self.response.context
