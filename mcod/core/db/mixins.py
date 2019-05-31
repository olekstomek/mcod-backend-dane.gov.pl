from collections import namedtuple

from django.db import models

from mcod import settings


class IndexableMixin(object):
    @property
    def is_indexable(self):
        return True


class CounterMixin(models.Model):
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True


class TranslationMixin(models.Model):
    _suffix = '_translated'

    def _get_field_trans_dict(self, field_name):
        _i18n = self._meta.get_field('i18n')
        if field_name not in _i18n.fields:
            raise ValueError(f'Field {field_name} does not support translations.')
        return {
            _lang: getattr(self, f'{field_name}_{_lang}') or getattr(self, f'{field_name}_i18n')
            for _lang in settings.MODELTRANS_AVAILABLE_LANGUAGES
        }

    def __getattr__(self, item):
        if item.endswith(self._suffix):
            item_name = item[:-len(self._suffix)]
            return type(item_name.capitalize(), (object,), self._get_field_trans_dict(item_name))()
        else:
            return super().__getattribute__(item)

    def get_translated_list(self, field, param):
        Translated = namedtuple('Translated', [lang for lang in settings.MODELTRANS_AVAILABLE_LANGUAGES])

        return [Translated(**{lang_code: (getattr(item, f'{param}_{lang_code}') or getattr(item, param))
                              for lang_code in settings.MODELTRANS_AVAILABLE_LANGUAGES})
                for item in getattr(self, field).all()]

    class Meta:
        abstract = True
