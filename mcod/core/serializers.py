from typing import Generator, Iterator, List

from django.db.models import QuerySet
from marshmallow.schema import BaseSchema, SchemaMeta, SchemaOpts
from more_itertools import chunked

from mcod.core.api import fields
from mcod.core.registries import csv_serializers_registry


class ModelSchemaOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.model_name = getattr(meta, "model", None)


class CSVSchemaRegistrator(SchemaMeta):
    def __new__(mcs, name, bases, attrs):
        klass = super().__new__(mcs, name, bases, attrs)
        csv_serializers_registry.register(klass)
        return klass


class CSVSerializer(BaseSchema):
    __doc__ = BaseSchema.__doc__
    OPTIONS_CLASS = ModelSchemaOpts
    QUERYSET_STREAM_CHUNK_SIZE = 1000

    def get_csv_headers(self) -> List[str]:
        result: List[str] = []
        for field_name, field in self.fields.items():
            header: str = field.data_key or field_name
            result.append(header)
        return result

    def _optimize_queryset(self, queryset: QuerySet) -> QuerySet:
        return queryset

    def stream_from_queryset(self, queryset: QuerySet) -> Generator[dict, None, None]:
        queryset: QuerySet = self._optimize_queryset(queryset)
        if queryset.ordered:
            queryset = queryset.order_by(*queryset.query.order_by, "pk")
        else:
            queryset = queryset.order_by("pk")
        chunk_size: int = self.QUERYSET_STREAM_CHUNK_SIZE
        queryset_iterator: Iterator = queryset.iterator(chunk_size=chunk_size)
        for chunk in chunked(queryset_iterator, chunk_size, strict=False):
            yield from self.dump(chunk, many=True)


class RDFSchema(BaseSchema, metaclass=SchemaMeta):
    __doc__ = BaseSchema.__doc__
    OPTIONS_CLASS = ModelSchemaOpts


class ListWithoutNoneStrElement(fields.List):
    @fields.after_serialize
    def remove_none(self, value=None):
        if isinstance(value, list) and "none" in value:
            return []
        return value
