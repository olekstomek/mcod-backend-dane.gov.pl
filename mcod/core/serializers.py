from marshmallow.schema import SchemaOpts, BaseSchema, SchemaMeta

from mcod.core.api import fields
from mcod.core.registries import csv_serializers_registry


class CSVSchemaMeta(SchemaMeta):
    def __new__(mcs, name, bases, attrs):
        klass = super(CSVSchemaMeta, mcs).__new__(mcs, name, bases, attrs)
        csv_serializers_registry.register(klass)
        return klass


class ModelSchemaOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.model_name = getattr(meta, 'model', None)


class RDFSchema(BaseSchema, metaclass=SchemaMeta):
    __doc__ = BaseSchema.__doc__
    OPTIONS_CLASS = ModelSchemaOpts


class CSVSerializer(BaseSchema, metaclass=CSVSchemaMeta):
    __doc__ = BaseSchema.__doc__
    OPTIONS_CLASS = ModelSchemaOpts

    def get_csv_headers(self):
        result = []
        for field_name, field in self.fields.items():
            header = field.data_key or field_name
            result.append(header)
        return result


class ListWithoutNoneStrElement(fields.List):
    @fields.after_serialize
    def remove_none(self, value=None):
        if isinstance(value, list) and 'none' in value:
            return []
        return value
