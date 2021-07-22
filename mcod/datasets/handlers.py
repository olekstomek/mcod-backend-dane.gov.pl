from functools import partial

from django.apps import apps

from mcod.core.api.handlers import RetrieveManyHdlr
from mcod.datasets.deserializers import DatasetResourcesDownloadApiRequest
from mcod.datasets.serializers import DatasetXMLSerializer, DatasetResourcesCSVSerializer


class CSVMetadataViewHandler(RetrieveManyHdlr):
    deserializer_schema = DatasetResourcesDownloadApiRequest
    database_model = apps.get_model('datasets', 'Dataset')
    serializer_schema = partial(DatasetResourcesCSVSerializer, many=True)

    def _get_data(self, cleaned, *args, **kwargs):
        return self._get_queryset(cleaned, *args, **kwargs).with_metadata_fetched()

    def prepare_context(self, *args, **kwargs):
        super().prepare_context(*args, **kwargs)
        self.response.context.serializer_schema = self.serializer

    def serialize(self, *args, **kwargs):
        self.prepare_context(*args, **kwargs)
        self.response.downloadable_as = '{}.csv'.format(kwargs.get('id', 'katalog'))
        return self.response.context


class XMLMetadataViewHandler(RetrieveManyHdlr):
    deserializer_schema = DatasetResourcesDownloadApiRequest
    database_model = apps.get_model('datasets', 'Dataset')
    serializer_schema = partial(DatasetXMLSerializer, many=True)

    def _get_data(self, cleaned, *args, **kwargs):
        return self._get_queryset(cleaned, *args, **kwargs).with_metadata_fetched()

    def prepare_context(self, *args, **kwargs):
        super().prepare_context(*args, **kwargs)
        self.response.context.serializer_schema = self.serializer

    def serialize(self, *args, **kwargs):
        self.prepare_context(*args, **kwargs)
        self.response.downloadable_as = '{}.xml'.format(kwargs.get('id', 'katalog'))
        return self.response.context
