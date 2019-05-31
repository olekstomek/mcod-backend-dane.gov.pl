from marshmallow import pre_load


class ESQuerySchemaMixin(object):
    def make_es_queryset(self, queryset, data):
        fields = getattr(self, 'fields', getattr(self, '_declared_fields', None))
        for field_name, field_obj in fields.items():
            queryset = field_obj.make_es_queryset(queryset, data.get(field_name))
        return queryset


class ESQueryFieldMixin(object):
    @property
    def _name(self):
        return getattr(self, 'data_key', getattr(self, 'name', None))

    def make_es_queryset(self, queryset, data):
        raise NotImplementedError


class ESFilterGTIntMixin(ESQueryFieldMixin):
    @pre_load
    def max_value(self, data):
        return data

    def make_es_queryset(self, queryset, data):
        return queryset
