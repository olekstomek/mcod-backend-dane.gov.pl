from collections import OrderedDict, defaultdict

from django.apps import apps


class FactoriesRegistry:
    def __init__(self):
        self._factories = defaultdict(OrderedDict)

    def register(self, object_name, serializer_cls):
        if object_name:
            self._factories[object_name] = serializer_cls

    def get_factory(self, object_name):
        return self._factories.get(object_name)


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
object_attrs_registry = SerializerRegistry()
rdf_serializers_registry = SerializerRegistry()

factories_registry = FactoriesRegistry()
