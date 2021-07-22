# from copy import copy
# from datetime import datetime
#
# from django.core.paginator import Page
# from django.utils.translation import get_language
# from marshmallow import class_registry, pre_dump
# from marshmallow import marshalling
# from marshmallow.base import SchemaABC
# from marshmallow.compat import basestring
# from marshmallow.decorators import (
#     POST_DUMP,
#     POST_LOAD,
#     PRE_DUMP,
#     PRE_LOAD,
#     VALIDATES_SCHEMA
# )
# from marshmallow.exceptions import ValidationError
# from querystring_parser import builder
#
# from mcod.core.api import fields
# from mcod.core.api import schemas
#
# json_api_object = {'version': '1.0'}
# empty_dict = {}
#
#
# class Nested(fields.Nested):
#     @property
#     def schema(self):
#         if not self.__schema:
#             context = getattr(self.parent, 'context', self.metadata.get('context', {}))
#             if isinstance(self.nested, SchemaABC):
#                 self.__schema = self.nested
#                 self.__schema.context = getattr(self.__schema, 'context', {})
#                 self.__schema.context.update(context)
#             else:
#                 if isinstance(self.nested, type) and issubclass(self.nested, SchemaABC):
#                     schema_class = self.nested
#                 elif not isinstance(self.nested, basestring):
#                     raise ValueError(
#                         'Nested fields must be passed a '
#                         'Schema, not {0}.'.format(self.nested.__class__),
#                     )
#                 elif self.nested == 'self':
#                     schema_class = self.parent.__class__
#                 else:
#                     schema_class = class_registry.get_class(self.nested)
#                 self.__schema = schema_class(
#                     many=self.many,
#                     only=self.only, exclude=self.exclude, context=context,
#                     load_only=self._nested_normalized_option('load_only'),
#                     dump_only=self._nested_normalized_option('dump_only'),
#                 )
#             self.__schema.ordered = getattr(self.parent, 'ordered', False)
#         return self.__schema
#
#
# class DummyAttributes(schemas.ExtSchema):
#     dummy = fields.Raw()
#
#
# class BaseLinks(schemas.ExtSchema):
#     self = fields.String(required=True)
#
#
# class BaseMeta(schemas.ExtSchema):
#     pass
#
#
# class ExtLinksMeta(schemas.ExtSchema):
#     count = fields.Integer()
#
#     class Meta:
#         nullable = True
#
#
# class ExtLinksSchema(schemas.ExtSchema):
#     href = fields.String(required=True)
#     meta = fields.Nested(ExtLinksMeta, name='meta')
#
#
# class BaseData(schemas.ExtSchema):
#     _type = fields.Str(data_key='type', attribute='type', required=True)
#     id = fields.Str(required=True)
#
#
# class RelationshipLinks(schemas.ExtSchema):
#     related = fields.Nested(ExtLinksSchema, name='related')
#
#     class Meta:
#         nullable = True
#
#
# class Relationship(schemas.ExtSchema):
#     links = fields.Nested(RelationshipLinks, name='links', required=True)
#
#     def __init__(
#             self, only=None, exclude=(), many=False, context=None,
#             load_only=(), dump_only=(), partial=False, unknown=None,
#     ):
#         super().__init__(only=only, exclude=exclude, many=many, context=context,
#                          load_only=load_only, dump_only=dump_only,
#                          partial=partial, unknown=unknown)
#         self.many = False
#         _meta = getattr(self, 'Meta', None)
#         data_cls = getattr(_meta, 'data_cls', BaseData)
#         self.fields['data'] = fields.Nested(data_cls, name='data')
#
#         meta_cls = getattr(_meta, 'meta_cls', BaseMeta)
#         if not issubclass(meta_cls, BaseMeta):
#             raise Exception("{} must be a subclass of BaseMeta".format(meta_cls.__class__))
#         self.fields['meta'] = fields.Nested(meta_cls, name='meta', required=False)
#
#     @pre_dump(pass_many=False)
#     def prepare_links(self, data):
#         path = getattr(self.Meta, '_path', 'unspecified')
#         setattr(data, 'links', {
#             'related': {
#                 'href': '{}/{}/{}'.format(self.api_url, path, data.id)
#             }
#         })
#         return data
#
#     class Meta:
#         meta_cls = BaseMeta
#         nullable = True
#
#
# class DummyRelationship(schemas.ExtSchema):
#     dummy = fields.Nested(Relationship, name='dummy')
#
#     class Meta:
#         nullable = True
#
#
# class ResponseLinksSingle(BaseLinks):
#     pass
#
#
# class ResponseLinksMany(BaseLinks):
#     first = fields.String(required=True)
#     prev = fields.String()
#     next = fields.String()
#     last = fields.String()
#     self = fields.String(required=True)
#
#
# class ResponseData(BaseData):
#     def __init__(
#             self, only=None, exclude=(), many=False, context=None,
#             load_only=(), dump_only=(), partial=False, unknown=None,
#     ):
#         super().__init__(only=only, exclude=exclude, many=many, context=context,
#                          load_only=load_only, dump_only=dump_only,
#                          partial=partial, unknown=unknown)
#
#         _meta = getattr(self, 'Meta', None)
#
#         rel_cls = getattr(_meta, 'relationship_cls', DummyRelationship)
#         links_cls = getattr(_meta, 'links_cls', BaseLinks)
#         meta_cls = getattr(_meta, 'meta_cls', BaseMeta)
#
#         _attr_cls = 'attr_short_cls' if many else 'attr_cls'
#         self.fields['attributes'] = fields.Nested(
#             getattr(_meta, _attr_cls, DummyAttributes), name='attributes')
#         if 'relationships' not in self.fields:
#             self.fields['relationships'] = fields.Nested(rel_cls, name='relationships')
#
#         self.fields['links'] = fields.Nested(links_cls, name='links')
#         self.fields['meta'] = fields.Nested(meta_cls, name='meta')
#         _type = getattr(_meta, '_type', None)
#
#         if _type:
#             self.fields['_type'] = fields.Str(required=True, missing=_type,
#                                               default=_type, data_key='type')
#
#     @pre_dump(pass_many=False)
#     def prepare_attributes(self, data):
#         setattr(data, 'attributes', data)
#         return data
#
#     @pre_dump(pass_many=False)
#     def prepare_links(self, data):
#         path = getattr(self.Meta, '_path', 'unspecified')
#         ident = data.id
#         if hasattr(data, 'slug'):
#             slug = getattr(data.slug, get_language(), data.slug)
#             ident = '{},{}'.format(ident, slug)
#         data.links = {
#             'self': '{}/{}/{}'.format(self.api_url, path, ident)
#         }
#
#         return data
#
#     class Meta:
#         attr_short_cls = DummyAttributes
#         attr_cls = DummyAttributes
#         relationship_cls = DummyRelationship
#         links_cls = BaseLinks
#         meta_cls = BaseMeta
#
#
# class ResponseMeta(schemas.ExtSchema):
#     server_time = fields.DateTime(missing=datetime.now(), default=datetime.now())
#     language = fields.Str(required=True, missing='en', default='en')
#     # params = fields.Dict(required=True, nullable=True)
#     path = fields.Str(required=True)
#     relative_uri = fields.Str(required=True)
#     count = fields.Integer()
#
#     def __init__(
#             self, only=None, exclude=(), many=False, context=None,
#             load_only=(), dump_only=(), partial=False, unknown=None,
#     ):
#         super().__init__(only=only, exclude=exclude, many=many, context=context,
#                          load_only=load_only, dump_only=dump_only,
#                          partial=partial, unknown=unknown)
#         many = self.context.get('many', False)
#         if many:
#             self.fields['count'] = fields.Int(required=True, missing=0, default=0)
#
#         _meta = getattr(self, 'Meta', None)
#         aggs_cls = getattr(_meta, 'aggregations_cls', None)
#
#         self.fields['aggregations'] = fields.Nested(aggs_cls, name='aggregations',
#                                                     required=False) if aggs_cls else fields.Dict(nullable=True)
#
#
# class ResponseSchema(schemas.ExtSchema):
#     jsonapi = fields.Raw(missing=json_api_object, default=json_api_object)
#     errors = fields.Raw(required=False)
#
#     def __init__(
#             self, only=None, exclude=(), many=False, context=None,
#             load_only=(), dump_only=(), partial=False, unknown=None,
#     ):
#         super().__init__(only=only, exclude=exclude, many=many, context=context,
#                          load_only=load_only, dump_only=dump_only,
#                          partial=partial, unknown=unknown)
#
#         # Top level links
#         links_cls = ResponseLinksMany if self.many else ResponseLinksSingle
#         self.fields['links'] = Nested(links_cls, name='links',
#                                       required=False, many=False, context={'many': self.many})
#
#         # Top level meta
#         _meta = getattr(self, 'Meta', None)
#         meta_cls = getattr(_meta, 'meta_cls', ResponseMeta)
#         if not issubclass(meta_cls, ResponseMeta):
#             raise Exception("{} must be a subclass of TopLevelMeta".format(meta_cls.__class__))
#         self.fields['meta'] = fields.Nested(meta_cls, name='meta', many=False,
#                                             context={'many': self.many},
#                                             required=False)
#
#         # Top level data
#         data_cls = getattr(_meta, 'data_cls', ResponseData)
#         if not issubclass(data_cls, ResponseData):
#             raise Exception("{} must be a subclass of ResponseData".format(data_cls.__class__))
#         self.fields['data'] = fields.Nested(data_cls, name='data', many=self.many, data_key='data')
#
#     def dump(self, obj, many=None):  # noqa:C901
#         marshaller = marshalling.Marshaller()
#         errors = {}
#         many = self.many if many is None else bool(many)
#         processed_obj = obj
#         result = None
#         if self._has_processors(PRE_DUMP):
#             try:
#                 processed_obj = self._invoke_dump_processors(
#                     PRE_DUMP,
#                     obj,
#                     many,
#                     original_data=obj,
#                 )
#             except ValidationError as error:
#                 errors = error.normalized_messages()
#
#         if not errors:
#             try:
#                 result = marshaller.serialize(
#                     processed_obj,
#                     self._fields,
#                     many=False,
#                     accessor=self.get_attribute,
#                     dict_class=self.dict_class,
#                     index_errors=self.opts.index_errors,
#                 )
#             except ValidationError as error:
#                 errors = marshaller.errors
#                 result = error.data
#
#         if not errors and self._has_processors(POST_DUMP):
#             try:
#                 result = self._invoke_dump_processors(
#                     POST_DUMP,
#                     result,
#                     many,
#                     original_data=obj,
#                 )
#             except ValidationError as error:
#                 errors = error.normalized_messages()
#         if errors:
#             error_field_names = getattr(marshaller, 'error_field_names', [])
#             exc = ValidationError(
#                 errors,
#                 field_names=error_field_names,
#                 data=obj,
#                 valid_data=result,
#                 **marshaller.error_kwargs
#             )
#             # User-defined error handler
#             self.handle_error(exc, obj)
#             raise exc
#
#         return result
#
#     def _do_load(  # noqa:C901
#             self, data, many=None, partial=None, unknown=None,
#             postprocess=True,
#     ):
#         errors = {}
#         result = None
#         processed_data = None
#         many = self.many if many is None else bool(many)
#         unknown = unknown or self.unknown
#         if partial is None:
#             partial = self.partial
#         if self._has_processors(PRE_LOAD):
#             try:
#                 processed_data = self._invoke_load_processors(
#                     PRE_LOAD,
#                     data,
#                     many,
#                     original_data=data,
#                 )
#             except ValidationError as err:
#                 errors = err.normalized_messages()
#         else:
#             processed_data = data
#         unmarshaller = marshalling.Unmarshaller()
#         if not errors:
#             result = unmarshaller.deserialize(
#                 processed_data,
#                 self._fields,
#                 many=False,
#                 partial=partial,
#                 unknown=unknown,
#                 dict_class=self.dict_class,
#                 index_errors=self.opts.index_errors,
#             )
#             self._invoke_field_validators(unmarshaller, data=result, many=False)
#             if self._has_processors(VALIDATES_SCHEMA):
#                 field_errors = bool(unmarshaller.errors)
#                 self._invoke_schema_validators(
#                     unmarshaller,
#                     pass_many=True,
#                     data=result,
#                     original_data=data,
#                     many=many,
#                     field_errors=field_errors,
#                 )
#                 self._invoke_schema_validators(
#                     unmarshaller,
#                     pass_many=False,
#                     data=result,
#                     original_data=data,
#                     many=many,
#                     field_errors=field_errors,
#                 )
#             errors = unmarshaller.errors
#             if not errors and postprocess and self._has_processors(POST_LOAD):
#                 try:
#                     result = self._invoke_load_processors(
#                         POST_LOAD,
#                         result,
#                         many,
#                         original_data=data,
#                     )
#                 except ValidationError as err:
#                     errors = err.normalized_messages()
#         if errors:
#             error_field_names = getattr(unmarshaller, 'error_field_names', [])
#             exc = ValidationError(
#                 errors,
#                 field_names=error_field_names,
#                 data=data,
#                 valid_data=result,
#                 **unmarshaller.error_kwargs
#             )
#             self.handle_error(exc, data)
#             raise exc
#
#         return result
#
#     @property
#     def _many(self):
#         return False
#
#
# class SearchResult(ResponseSchema):
#     @pre_dump(pass_many=True)
#     def make_toplevel_links(self, data, many):
#         def get_pagination_link(page_num):
#             cleaned['page'] = page_num
#             return '{}{}?{}'.format(request.prefix, request.path, builder.build(cleaned))
#
#         request = self.context['request']
#         cleaned = copy(request.context.cleaned_data)
#
#         links = {
#             'self': request.uri
#         }
#         if many:
#             page, per_page = cleaned.get('page', 1), cleaned.get('per_page', 20)
#             links['self'] = get_pagination_link(page)
#             links['first'] = get_pagination_link(1)
#             if isinstance(data, Page):
#                 items_count = data.result.paginator.count
#             else:
#                 items_count = data.result.hits.total if \
#                     hasattr(data.result, 'hits') else 0
#             if page > 1:
#                 links['prev'] = get_pagination_link(page - 1)
#             if items_count:
#                 m = 1 if items_count % per_page else 0
#                 last_page = items_count // per_page + m
#                 if last_page > 1:
#                     links['last'] = get_pagination_link(last_page)
#                 if page * per_page < items_count:
#                     links['next'] = get_pagination_link(page + 1)
#         data.links = links
#         return data
#
#     @pre_dump(pass_many=True)
#     def make_meta(self, data, many):
#         request = self.context['request']
#         meta = getattr(request.context, 'meta', {})
#         meta.update({
#             'language': request.language,
#             'params': request.params,
#             'path': request.path,
#             'relative_uri': request.relative_uri,
#             'aggregations': getattr(data.result, 'aggregations', {})
#         })
#
#         if many:
#             meta['aggregations'] = getattr(data.result, 'aggregations', {})
#             if isinstance(data, Page):
#                 meta['count'] = data.result.paginator.count
#             else:
#                 meta['count'] = data.result.hits.total \
#                     if hasattr(data.result, 'hits') else 0
#
#         data.meta = meta
#         return data
#
#     class Meta:
#         meta_cls = ResponseMeta
#         data_cls = ResponseData
#
#
# class Aggregation(schemas.ExtSchema):
#     key = fields.Raw()
#     title = fields.String()
#     doc_count = fields.Integer()
#
#
# class SearchAggregation(Aggregation):
#     @pre_dump(pass_many=True)
#     def prepare_data(self, data, many):
#         return [
#             {
#                 'key': item['key'],
#                 'title': item['key'],
#                 'doc_count': item['doc_count']
#             } for item in data
#         ]
#
#
# class ModelAggregation(Aggregation):
#     @pre_dump(pass_many=True)
#     def prepare_data(self, data, many):
#         _meta = getattr(self, 'Meta')
#         model = getattr(_meta, 'model', None)
#         ret = []
#
#         if model:
#             objects = self.model.raw.filter(pk__in=[item['key'] for item in data])
#             for item in data:
#                 try:
#                     obj = objects.get(pk=item['key'])
#                     item['title'] = getattr(obj, 'title', None)
#                     ret.append(item)
#                 except model.DoesNotExist:
#                     pass
#         return ret
#
#     class Meta:
#         model = None
#
#
# class REQData(schemas.ExtSchema):
#     _type = fields.Str(data_key='type', attribute='type', required=True)
#
#     def __init__(
#             self, only=None, exclude=(), many=False, context=None,
#             load_only=(), dump_only=(), partial=False, unknown=None,
#     ):
#         super().__init__(only=only, exclude=exclude, many=many, context=context,
#                          load_only=load_only, dump_only=dump_only,
#                          partial=partial, unknown=unknown)
#
#         _meta = getattr(self, 'Meta', None)
#
#         rel_cls = getattr(_meta, 'relationships_cls', DummyRelationship)
#         self.fields['attributes'] = fields.Nested(
#             getattr(_meta, 'attrs_cls', DummyAttributes), name='attributes')
#         if 'relationships' not in self.fields:
#             self.fields['relationships'] = fields.Nested(rel_cls, name='relationships')
#
#         _type = getattr(_meta, '_type', None)
#
#         if _type:
#             self.fields['_type'] = fields.Str(required=True, missing=_type,
#                                               default=_type, data_key='type')
#
#     @pre_dump(pass_many=False)
#     def prepare_attributes(self, data):
#         setattr(data, 'attributes', data)
#         return data
#
#
# class POSTData(REQData):
#     class Meta:
#         pass
#
#
# class PATCHData(REQData):
#     id = fields.Str(required=True)
#
#     class Meta:
#         pass
#
#
# class REQSchema(schemas.CommonSchema):
#     def __init__(
#             self, only=None, exclude=(), many=False, context=None,
#             load_only=(), dump_only=(), partial=False, unknown=None,
#     ):
#         super().__init__(only=only, exclude=exclude, many=many, context=context,
#                          load_only=load_only, dump_only=dump_only,
#                          partial=partial, unknown=unknown)
#
#         _meta = getattr(self, 'Meta', None)
#
#         if not issubclass(self._data_cls, REQData):
#             raise Exception("{} must be a subclass of ResponseData".format(self._data_cls.__class__))
#
#         setattr(self._data_cls.Meta, 'attrs_cls', getattr(_meta, 'attrs_cls', DummyAttributes))
#         setattr(self._data_cls.Meta, 'relationship_cls', getattr(_meta, 'relationship_cls', DummyRelationship))
#         setattr(self._data_cls.Meta, '_type', getattr(_meta, '_type', None))
#
#         self.fields['data'] = fields.Nested(self._data_cls,
#                                             name='data',
#                                             many=self.many,
#                                             data_key='data')
#
#
# class POSTSchema(REQSchema):
#     _data_cls = POSTData
#
#     class Meta:
#         pass
#
#
# class PATCHSchema(REQSchema):
#     _data_cls = PATCHData
#
#     class Meta:
#         pass
