from marshmallow import class_registry
from marshmallow.base import SchemaABC

from mcod.core.api import fields


class Nested(fields.Nested):
    @property
    def schema(self):
        if not self.__schema:
            context = getattr(self.parent, 'context', self.metadata.get('context', {}))
            if isinstance(self.nested, SchemaABC):
                self.__schema = self.nested
                self.__schema.context = getattr(self.__schema, 'context', {})
                self.__schema.context.update(context)
            else:
                if isinstance(self.nested, type) and issubclass(self.nested, SchemaABC):
                    schema_class = self.nested
                elif not isinstance(self.nested, (str, bytes)):
                    raise ValueError(
                        'Nested fields must be passed a '
                        'Schema, not {0}.'.format(self.nested.__class__),
                    )
                elif self.nested == 'self':
                    schema_class = self.parent.__class__
                else:
                    schema_class = class_registry.get_class(self.nested)
                self.__schema = schema_class(
                    many=self.many,
                    only=self.only, exclude=self.exclude, context=context,
                    load_only=self._nested_normalized_option('load_only'),
                    dump_only=self._nested_normalized_option('dump_only'),
                )
            self.__schema.ordered = getattr(self.parent, 'ordered', False)
        return self.__schema
