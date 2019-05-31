from marshmallow import SchemaOpts

from mcod.core.api import schemas, fields


class ObjectAttrsOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.object_type = getattr(meta, 'object_type', None) or 'undefined'


class ObjectAttrs(schemas.ExtSchema):
    OPTIONS_CLASS = ObjectAttrsOpts


class ObjectOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.attrs_schema = getattr(meta, 'attrs_schema', None)
        if self.attrs_schema and not issubclass(self.attrs_schema, ObjectAttrs):
            raise Exception("{} must be a subclass of ObjectAttrs".format(self.attrs_schema))


class Object(schemas.ExtSchema):
    OPTIONS_CLASS = ObjectOpts
    _type = fields.String(required=True, data_key='type')

    def __init__(
            self, only=None, exclude=(), many=False, context=None,
            load_only=(), dump_only=(), partial=False, unknown=None,
    ):
        self._declared_fields['attributes'] = fields.Nested(
            self.opts.attrs_schema, name='attributes', many=False
        )

        # relationships_schema = getattr(self.opts.attrs_schema.opts, 'relationships_schema', None)
        #
        # if relationships_schema:
        #     self._declared_fields['relationships'] = fields.Nested(relationships_schema, many=False,
        #                                                            name='relationships')

        super().__init__(only=only, exclude=exclude, many=many, context=context,
                         load_only=load_only, dump_only=dump_only,
                         partial=partial, unknown=unknown)


class ObjectWithId(Object):
    id = fields.Str(required=True)


class TopLevelOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.attrs_schema = getattr(meta, 'attrs_schema', None)

        if self.attrs_schema and not issubclass(self.attrs_schema, ObjectAttrs):
            raise Exception("{} must be a subclass of ObjectAttrs".format(self.attrs_schema))

        self.object_schema = getattr(meta, 'object_schema', Object)

        if self.object_schema and not issubclass(self.object_schema, Object):
            raise Exception("{} must be a subclass of Object".format(self.object_schema))


class TopLevel(schemas.ExtSchema):
    OPTIONS_CLASS = TopLevelOpts

    def __init__(
            self, only=None, exclude=(), many=False, context=None,
            load_only=(), dump_only=(), partial=False, unknown=None,
    ):
        data_cls = type(
            '{}Data'.format(self.__class__.__name__),
            (self.opts.object_schema,), {}
        )
        setattr(data_cls.opts, 'attrs_schema', self.opts.attrs_schema)

        self._declared_fields['data'] = fields.Nested(data_cls, name='data', many=False)

        super().__init__(only=only, exclude=exclude, many=False, context=context,
                         load_only=load_only, dump_only=dump_only,
                         partial=partial, unknown=unknown)
