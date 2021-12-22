from collections import namedtuple

from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe

from mcod.core.api.jsonapi.serializers import Object
from mcod.core.api.jsonapi.serializers import object_attrs_registry as oar
from mcod import settings


class AdminMixin(object):

    @property
    def admin_change_url(self):
        if self.id:
            return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=(self.id,))
        return ''

    def mark_safe(self, value):
        return mark_safe(value)


class ApiMixin(object):

    @property
    def ident(self):
        return '{},{}'.format(self.id, self.slug) if (hasattr(self, 'slug') and self.slug) else self.id

    @property
    def api_url(self):
        return self.get_api_url()

    @property
    def api_url_base(self):
        return self._meta.app_label

    def get_api_url(self, base_url=settings.API_URL):
        if not self.id:
            return None

        return '{}/{}/{}'.format(base_url, self.api_url_base, self.ident)

    def to_jsonapi(self, _schema=None, api_version=None):
        _schema = _schema or oar.get_serializer(self.__class__)
        data_cls = type(
            '{}Data'.format(self.__class__.__name__),
            (Object,), {}
        )
        setattr(data_cls.opts, 'attrs_schema', _schema)
        return data_cls(many=False, context={'api_version': api_version}).dump(self)

    @classmethod
    def _get_included(cls, ids, **kwargs):
        order_by = kwargs.pop('order_by', None)
        qs = cls.objects.filter(id__in=ids)
        return qs.order_by(*order_by) if isinstance(order_by, tuple) else qs

    @classmethod
    def get_included(cls, ids, **kwargs):
        api_version = kwargs.pop('api_version', None)
        return [x for x in (x.to_jsonapi(api_version=api_version) for x in cls._get_included(ids, **kwargs)) if x]


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
