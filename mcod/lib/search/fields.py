from django_elasticsearch_dsl import fields

from mcod import settings
from mcod.core.api.search.analyzers import polish_analyzer, polish_asciied, standard_asciied
from mcod.core.api.search.fields import ICUSortField


class TranslatedTextField(fields.NestedField):
    asciied = {
        'pl': polish_asciied,
    }

    def __init__(self, field_name, common_params=None, std_params=True, *args, **kwargs):
        _params = common_params or {}
        _properties = {
            lang_code: fields.TextField(
                fields={
                    'raw': fields.KeywordField(),
                    'sort': ICUSortField(index=False, language=lang_code, country=lang_code.upper()),
                    'asciied': fields.TextField(analyzer=self.asciied.get(lang_code, standard_asciied)),
                    **_params
                } if std_params else common_params
            ) for lang_code in settings.MODELTRANS_AVAILABLE_LANGUAGES
        }

        _properties['pl'].analyzer = polish_analyzer
        if 'properties' in kwargs:
            _properties.update(kwargs['properties'])
            del kwargs['properties']

        super().__init__(attr=f'{field_name}_translated', properties=_properties, *args, **kwargs)


class TranslatedKeywordField(fields.NestedField):
    def __init__(self, field_name, common_params=None, *args, **kwargs):
        _params = common_params or {}
        _properties = {
            lang_code: fields.KeywordField(**_params)
            for lang_code in settings.MODELTRANS_AVAILABLE_LANGUAGES
        }

        if 'properties' in kwargs:
            _properties.update(kwargs['properties'])
            del kwargs['properties']

        super().__init__(attr=f'{field_name}_translated', properties=_properties, *args, **kwargs)


class TranslatedKeywordsList(fields.NestedField):
    def __init__(self, common_params=None, *args, **kwargs):
        _params = common_params or {}
        _properties = {
            lang_code: fields.KeywordField(**_params)
            for lang_code in settings.MODELTRANS_AVAILABLE_LANGUAGES
        }

        if 'properties' in kwargs:
            _properties.update(kwargs['properties'])
            del kwargs['properties']

        if 'multi' in kwargs:
            del kwargs['multi']

        super().__init__(properties=_properties, multi=True, *args, **kwargs)
