from collections import OrderedDict, defaultdict

from django.apps import apps
from marshmallow.compat import with_metaclass
from marshmallow.schema import SchemaOpts, BaseSchema, SchemaMeta


class SerializerRegistry:
    def __init__(self):
        self._serializers = defaultdict(OrderedDict)

    def register(self, serializer_cls):
        _name = serializer_cls.opts.model_name
        if _name:
            _app, _model = _name.split('.')
            model = apps.get_model(_app, _model)
            self._serializers[model] = serializer_cls

    def get_serializer(self, model):
        return self._serializers.get(model)


csv_serializers_registry = SerializerRegistry()


class CSVSchemaMeta(SchemaMeta):
    def __new__(mcs, name, bases, attrs):
        klass = super(CSVSchemaMeta, mcs).__new__(mcs, name, bases, attrs)
        csv_serializers_registry.register(klass)
        return klass


class CSVSerializerOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.model_name = getattr(meta, 'model', None)


class CSVSerializer(with_metaclass(CSVSchemaMeta, BaseSchema)):
    __doc__ = BaseSchema.__doc__
    OPTIONS_CLASS = CSVSerializerOpts
