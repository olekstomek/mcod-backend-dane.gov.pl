from collections.abc import Sequence

from django.core import paginator
from django.db.models import QuerySet
from django.utils.timezone import now
from django.utils.translation import get_language
from elasticsearch_dsl import InnerDoc, AttrList
from marshmallow import pre_dump
from marshmallow.schema import SchemaOpts
from querystring_parser import builder

from mcod.core.api import schemas, fields
from mcod.core.serializers import SerializerRegistry

object_attrs_registry = SerializerRegistry()


class RelationshipData(schemas.ExtSchema):
    id = fields.String(required=True)
    _type = fields.String(required=True, data_key='type')


class RelationshipLinks(schemas.ExtSchema):
    related = fields.String(required=True)


class RelationshipMeta(schemas.ExtSchema):
    count = fields.Integer()


class Relationship(schemas.ExtSchema):
    data = fields.Nested(RelationshipData)
    links = fields.Nested(RelationshipLinks, required=True, many=False)
    meta = fields.Nested(RelationshipMeta, many=False)

    @pre_dump
    def prepare_data(self, data):
        object_url = self.context.get('object_url', None) or self.api_url
        url_template = self.context.get('url_template') or None
        res = {}
        if isinstance(data, (Sequence, QuerySet, AttrList)):
            if url_template:
                related_url = url_template.format(
                    api_url=self.api_url, object_url=object_url
                )
                res['links'] = {
                    'related': related_url
                }
            res['meta'] = {
                'count': len(data)
            }
        else:
            ident = getattr(data, 'id', None) or getattr(data.meta, 'id')
            slug = getattr(data, 'slug', None)
            if isinstance(slug, InnerDoc):
                lang = get_language()
                slug = slug[lang]
            if slug:
                ident = '{},{}'.format(ident, slug)
            if url_template:
                related_url = url_template.format(
                    api_url=self.api_url, object_url=object_url, ident=ident
                )
                res['links'] = {
                    'related': related_url
                }
            res['data'] = {
                'id': ident,
                '_type': self.context['_type']
            }

        return res


class Relationships(schemas.ExtSchema):
    def __init__(
            self, only=None, exclude=(), many=False, context=None,
            load_only=(), dump_only=(), partial=False, unknown=None,
    ):
        super().__init__(only=only, exclude=exclude, many=many, context=context,
                         load_only=load_only, dump_only=dump_only,
                         partial=partial, unknown=unknown)

        for field_name, field in self.fields.items():
            field._schema.context = dict(self.context)
            field._schema.context.update(field.metadata)
            field.many = False


class ObjectAttrsMeta(schemas.ExtSchema):
    pass


class ObjectAttrsOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.relationships_schema = getattr(meta, 'relationships_schema', None)

        if self.relationships_schema and not issubclass(self.relationships_schema, Relationships):
            raise Exception("{} must be a subclass of Relationships".format(self.relationships_schema))

        self.meta_schema = getattr(meta, 'meta_schema', None)

        if self.meta_schema and not issubclass(self.meta_schema, ObjectAttrsMeta):
            raise Exception("{} must be a subclass of ObjectAttrsMeta".format(self.meta_schema))

        self.object_type = getattr(meta, 'object_type', None) or 'undefined'
        self.model_name = getattr(meta, 'model', None) or None
        self.url_template = getattr(meta, 'url_template', None) or '{api_url}'


class ObjectAttrs(schemas.ExtSchema):
    OPTIONS_CLASS = ObjectAttrsOpts

    @classmethod
    def prepare(cls):
        object_attrs_registry.register(cls)


class ObjectLinks(schemas.ExtSchema):
    self = fields.String(required=True)


class ObjectOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.attrs_schema = getattr(meta, 'attrs_schema', None)
        if self.attrs_schema and not issubclass(self.attrs_schema, ObjectAttrs):
            raise Exception("{} must be a subclass of ObjectAttrs".format(self.attrs_schema))


class Object(schemas.ExtSchema):
    OPTIONS_CLASS = ObjectOpts
    id = fields.Str(required=True)
    links = fields.Nested(ObjectLinks, name='links')
    _type = fields.String(required=True, data_key='type')

    # meta = fields.Nested(ObjectMeta)

    def __init__(
            self, only=None, exclude=(), many=False, context=None,
            load_only=(), dump_only=(), partial=False, unknown=None,
    ):

        self._declared_fields['attributes'] = fields.Nested(
            self.opts.attrs_schema, name='attributes', many=False
        )

        relationships_schema = getattr(self.opts.attrs_schema.opts, 'relationships_schema', None)

        if relationships_schema:
            self._declared_fields['relationships'] = fields.Nested(relationships_schema, many=False,
                                                                   name='relationships')

        meta_schema = getattr(self.opts.attrs_schema.opts, 'meta_schema', None)

        if meta_schema:
            self._declared_fields['meta'] = fields.Nested(meta_schema, many=False,
                                                          name='meta')

        super().__init__(only=only, exclude=exclude, many=many, context=context,
                         load_only=load_only, dump_only=dump_only,
                         partial=partial, unknown=unknown)

    @pre_dump(pass_many=False)
    def prepare_data(self, data):
        ident = getattr(data, 'id', None) or getattr(data.meta, 'id')
        slug = getattr(data, 'slug', None)
        if isinstance(slug, InnerDoc):
            lang = get_language()
            slug = slug[lang]
        if slug:
            ident = '{},{}'.format(ident, slug)

        res = dict(
            attributes=data,
            id=str(ident),
            _type=self.opts.attrs_schema.opts.object_type
        )
        object_url = self.opts.attrs_schema.opts.url_template.format(
            api_url=self.api_url,
            ident=ident,
            data=data
        )
        res['links'] = {
            'self': object_url
        }

        if 'meta' in self._declared_fields:
            res['meta'] = data

        if 'relationships' in self.fields:
            relationships = {}
            for name, field in self.fields['relationships'].schema.fields.items():
                _name = field.attribute or name
                field._schema.context.update(object_url=object_url)
                value = getattr(data, _name, None)
                if value:
                    relationships[_name] = value
            if relationships:
                res['relationships'] = relationships
        return res


class TopLevelMeta(schemas.ExtSchema):
    language = fields.String()
    params = fields.Raw()
    path = fields.String()
    count = fields.Integer()
    relative_uri = fields.String()
    aggregations = fields.Raw()
    server_time = fields.DateTime(default=now)


class TopLevelLinks(schemas.ExtSchema):
    self = fields.String()
    first = fields.String()
    last = fields.String()
    prev = fields.String()
    next = fields.String()


class TopLevelOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.attrs_schema = getattr(meta, 'attrs_schema', None)
        self.aggs_schema = getattr(meta, 'aggs_schema', None)

        # self.errors_schema = getattr(meta, 'errors_schema', ResponseErrors)
        self.meta_schema = getattr(meta, 'meta_schema', TopLevelMeta)
        self.links_schema = getattr(meta, 'links_schema', TopLevelLinks)

        self.max_items_num = getattr(meta, 'max_items_num', 10000)

        if self.attrs_schema and not issubclass(self.attrs_schema, ObjectAttrs):
            raise Exception("{} must be a subclass of ObjectAttrs".format(self.attrs_schema))
        if self.meta_schema and not issubclass(self.meta_schema, TopLevelMeta):
            raise Exception("{} must be a subclass of Meta".format(self.meta_schema))
        if self.aggs_schema:
            if not issubclass(self.aggs_schema, schemas.ExtSchema):
                raise Exception("{} must be a subclass of ExtSchema".format(self.aggs_schema))
            self.meta_schema.aggregations = fields.Nested(self.aggs_schema, many=False)
        if self.links_schema and not issubclass(self.links_schema, TopLevelLinks):
            raise Exception("{} must be a subclass of Links".format(self.links_schema))


class Aggregation(schemas.ExtSchema):
    id = fields.String(attribute='key')
    title = fields.String()
    doc_count = fields.Integer()

    @pre_dump(pass_many=True)
    def prepare_data(self, data, many):
        if many:
            for item in data:
                item['title'] = str(item.key).upper()
            return data


class TopLevel(schemas.ExtSchema):
    included = fields.Raw()
    jsonapi = fields.Raw(default={'version': '1.0'})
    errors = fields.Raw()

    OPTIONS_CLASS = TopLevelOpts

    def __init__(
            self, only=None, exclude=(), many=False, context=None,
            load_only=(), dump_only=(), partial=False, unknown=None,
    ):
        data_cls = type(
            '{}Data'.format(self.__class__.__name__),
            (Object,), {}
        )
        setattr(data_cls.opts, 'attrs_schema', self.opts.attrs_schema)

        self._declared_fields['data'] = fields.Nested(data_cls, name='data', many=many)

        if self.opts.meta_schema:
            if self.opts.aggs_schema:
                self.opts.meta_schema._declared_fields['aggregations'] = fields.Nested(self.opts.aggs_schema,
                                                                                       many=False)
            self._declared_fields['meta'] = fields.Nested(
                self.opts.meta_schema, name='meta', many=False
            )

        if self.opts.links_schema:
            self._declared_fields['links'] = fields.Nested(
                self.opts.links_schema, name='links', many=False
            )
        context = context or {}
        context['is_listing'] = many

        super().__init__(only=only, exclude=exclude, many=False, context=context,
                         load_only=load_only, dump_only=dump_only,
                         partial=partial, unknown=unknown)

    @pre_dump
    def prepare_top_level(self, c):
        def _get_page_link(page_number):
            cleaned_data['page'] = page_number
            return '{}{}?{}'.format(request.prefix, request.path, builder.build(cleaned_data))

        c.data = getattr(c, 'data', {})
        request = self.context['request']
        c.meta = getattr(c, 'meta', {})
        c.links = getattr(c, 'links', {})
        cleaned_data = dict(request.context.cleaned_data)

        c.meta.update({
            'language': request.language,
            'params': request.params,
            'path': request.path,
            'relative_uri': request.relative_uri,
        })

        c.links['self'] = request.uri

        if self.context['is_listing']:
            c.meta['aggregations'] = getattr(c.data, 'aggregations', {}) or {}
            if isinstance(c.data, paginator.Page):
                items_count = c.data.paginator.count
            else:
                items_count = c.data.hits.total \
                    if hasattr(c.data, 'hits') else 0
            c.meta['count'] = items_count
            page, per_page = cleaned_data.get('page', 1), cleaned_data.get('per_page', 20)
            c.links['self'] = _get_page_link(page)
            if page > 1:
                c.links['first'] = _get_page_link(1)
                c.links['prev'] = _get_page_link(page - 1)
            if items_count:
                max_count = min(items_count, self.opts.max_items_num)
                off = 1 if max_count % per_page else 0
                last_page = max_count // per_page + off
                if last_page > 1:
                    c.links['last'] = _get_page_link(last_page)
                if page * per_page < max_count:
                    c.links['next'] = _get_page_link(page + 1)
        return c
