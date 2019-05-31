import marshmallow as ma
import marshmallow_jsonapi as ja
from django.apps import apps
from django.db.models.manager import BaseManager
from elasticsearch_dsl.document import InnerDoc
from elasticsearch_dsl.utils import AttrList
from django.utils.translation import get_language
from mcod.core.api import fields


class BucketItem(ma.Schema):
    key = ma.fields.Raw()
    title = ma.fields.String()
    doc_count = ma.fields.Integer()

    def __init__(
            self, app=None, model=None, only=None, exclude=(), many=False, context=None,
            load_only=(), dump_only=(), partial=False, unknown=None,
    ):
        super().__init__(only=only, exclude=exclude, many=many,
                         context=context, load_only=load_only, dump_only=dump_only, partial=partial, unknown=unknown)

        self.orm_model = apps.get_model(app, model) if app and model else None

    @ma.pre_dump(pass_many=True)
    def update_item(self, data, many):

        _valid_model = self.orm_model and hasattr(self.orm_model, 'title')
        if _valid_model:
            objects = self.orm_model.raw.filter(pk__in=[item['key'] for item in data])
        ret = []
        for item in data:
            if _valid_model:
                try:
                    obj = objects.get(pk=item['key'])
                    item['title'] = getattr(obj, 'title_i18n', obj.title)
                    ret.append(item)
                except self.orm_model.DoesNotExist:
                    pass
            else:
                item['title'] = item['key']
                ret.append(item)

        return ret


class BasicSerializer(ja.Schema):
    document_meta = ja.fields.DocumentMeta()

    def __init__(
            self, include_data=None, only=None, exclude=(), many=False, context=None,
            load_only=(), dump_only=(), partial=False, unknown=None,
    ):
        super().__init__(include_data=include_data, only=only, exclude=exclude, many=many, context=context,
                         load_only=load_only, dump_only=dump_only, partial=partial,
                         unknown=unknown)
        self.links = {}

    def dump(self, data, meta=None, links=None, many=None):
        self.included_data = {}
        self.document_meta = meta if meta else self.document_meta
        self.links = links or {}
        return super().dump(data, many=many)

    def wrap_response(self, data, many):
        return {
            'data': data,
            'links': self.links
        }


class ArgsListToDict(ma.Schema):
    @ma.pre_dump
    def prepare_data(self, obj):
        return obj.to_dict()


class SearchMeta(ma.Schema):
    count = ma.fields.Integer(missing=0, attribute='hits.total')
    took = ma.fields.Integer(missing=0, attribute='took')
    max_score = ma.fields.Float(attribute='hits.max_score')


class TranslatedStr(fields.String):
    def _serialize(self, value, attr, obj):
        lang = get_language()
        if value and isinstance(value, (InnerDoc, dict)):
            value = getattr(value, lang) or value.pl
        else:
            attr = '{}_{}'.format(attr, lang)
            value = getattr(obj, attr) or value
        return super()._serialize(value, attr, obj)


class TranslatedTagsList(fields.List):
    def serialize(self, attr, obj, accessor=None, **kwargs):
        _rel = getattr(obj, attr)
        if isinstance(_rel, BaseManager):
            return [i.name_i18n for i in _rel.all()]
        elif isinstance(_rel, AttrList):
            lang = get_language()
            return [i[lang] for i in _rel]
        return super().serialize(obj, attr, accessor=accessor)
