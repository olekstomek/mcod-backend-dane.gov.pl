import base64
import binascii
import functools
import inspect
import operator
from collections import defaultdict
from functools import partial

import markdown2
from django.template import loader
from django.utils.translation import gettext as _
from marshmallow import fields, missing
from marshmallow import utils
from marshmallow.orderedset import OrderedSet

from mcod.core import utils as api_utils

BEFORE_DESERIALIZE = 'before_deserialize'
BEFORE_SERIALIZE = 'before_serialize'
AFTER_DESERIALIZE = 'after_deserialize'
AFTER_SERIALIZE = 'after_serialize'

common_error_messages = {
    'required': _('Missing data for required field.'),
    'null': _('Field may not be null.'),
    'validator_failed': _('Invalid value.'),
}


def set_hook(fn, key, **kwargs):
    if fn is None:
        return partial(set_hook, key=key, **kwargs)
    try:
        hook_config = fn.__field_hook__
    except AttributeError:
        fn.__field_hook__ = hook_config = {}
    hook_config[key] = kwargs
    return fn


def before_serialize(fn, attr=None, obj=None, accessor=None):
    return set_hook(fn, 'before_serialize', attr=attr, obj=obj, accessor=accessor)


def before_deserialize(fn, value=None, attr=None, data=None):
    return set_hook(fn, 'before_deserialize', value=value, attr=attr, data=data)


def after_serialize(fn, value=None):
    return set_hook(fn, 'after_serialize', value=value)


def after_deserialize(fn, output=None):
    return set_hook(fn, 'after_deserialize', output=output)


class ExtendedFieldMeta(type):

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls._hooks = cls.resolve_hooks()
        cls.default_error_messages = getattr(cls, 'default_error_messages', {})
        cls.default_error_messages.update(common_error_messages)

    def resolve_hooks(self):
        mro = inspect.getmro(self)
        hooks = defaultdict(list)

        for attr_name in dir(self):
            for parent in mro:
                try:
                    attr = parent.__dict__[attr_name]
                except KeyError:
                    continue
                else:
                    break
            else:
                continue
            try:
                hook_config = attr.__field_hook__
            except AttributeError:
                pass
            else:
                for key in hook_config.keys():
                    hooks[key].append(attr_name)
        return hooks


class ExtendedFieldMixin(metaclass=ExtendedFieldMeta):
    @property
    def _missing(self):
        return missing

    @property
    def _validators(self):
        return getattr(self, 'validators', list())

    @property
    def _dump_only(self):
        return getattr(self, 'dump_only', False)

    @property
    def _load_only(self):
        return getattr(self, 'load_only', False)

    @property
    def _metadata(self):
        return getattr(self, 'metadata', dict())

    @property
    def _required(self):
        return getattr(self, 'required', False)

    @property
    def _allow_none(self):
        return getattr(self, 'allow_none', True)

    @property
    def _nested(self):
        return getattr(self, 'nested', False)

    @property
    def _many(self):
        return getattr(self, 'many', False)

    @property
    def _container(self):
        return getattr(self, 'container', None)

    @property
    def _value_container(self):
        return getattr(self, 'value_container', None)

    @property
    def _schema(self):
        return getattr(self, 'schema', None)

    @property
    def _name(self):
        return getattr(self, 'data_key') or getattr(self, 'name')

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'string'
        return ret

    def __to_choices(self):
        attributes = {}

        comparable = [
            validator.comparable for validator in self._validators
            if hasattr(validator, 'comparable')
        ]
        if comparable:
            attributes['enum'] = comparable
        else:
            choices = [
                OrderedSet(validator.choices) for validator in self._validators
                if hasattr(validator, 'choices')
            ]
            if choices:
                attributes['enum'] = list(functools.reduce(operator.and_, choices))

        return attributes

    def __to_range(self):
        validators = [
            validator for validator in self._validators
            if (
                    hasattr(validator, 'min') and
                    hasattr(validator, 'max') and
                    not hasattr(validator, 'equal')
            )
        ]

        attributes = {}
        for validator in validators:
            if validator.min is not None:
                if hasattr(attributes, 'minimum'):
                    attributes['minimum'] = max(
                        attributes['minimum'],
                        validator.min,
                    )
                else:
                    attributes['minimum'] = validator.min
            if validator.max is not None:
                if hasattr(attributes, 'maximum'):
                    attributes['maximum'] = min(
                        attributes['maximum'],
                        validator.max,
                    )
                else:
                    attributes['maximum'] = validator.max
        return attributes

    def __to_length(self):
        attributes = {}

        validators = [
            validator for validator in self._validators
            if (
                    hasattr(validator, 'min') and
                    hasattr(validator, 'max') and
                    hasattr(validator, 'equal')
            )
        ]

        is_array = isinstance(
            self, (
                fields.Nested,
                fields.List,
            ),
        )
        min_attr = 'minItems' if is_array else 'minLength'
        max_attr = 'maxItems' if is_array else 'maxLength'

        for validator in validators:
            if validator.min is not None:
                if hasattr(attributes, min_attr):
                    attributes[min_attr] = max(
                        attributes[min_attr],
                        validator.min,
                    )
                else:
                    attributes[min_attr] = validator.min
            if validator.max is not None:
                if hasattr(attributes, max_attr):
                    attributes[max_attr] = min(
                        attributes[max_attr],
                        validator.max,
                    )
                else:
                    attributes[max_attr] = validator.max

        for validator in validators:
            if validator.equal is not None:
                attributes[min_attr] = validator.equal
                attributes[max_attr] = validator.equal
        return attributes

    def _prepare_openapi_property(self):
        attributes = {}

        if 'example' in self._metadata:
            attributes['example'] = self._metadata['example']

        description = self._metadata.get('description', '')
        if description:
            attributes['description'] = description

        if self._dump_only:
            attributes['readOnly'] = True

        if self._load_only:
            attributes['writeOnly'] = True

        if 'doc_default' in self._metadata:
            attributes['default'] = self._metadata['doc_default']
        else:
            default = self._missing
            if default is not missing and not callable(default):
                attributes['default'] = default

        if self._allow_none:
            attributes['nullable'] = True

        attributes.update(self.__to_choices())
        attributes.update(self.__to_range())
        attributes.update(self.__to_length())

        return attributes

    def make_doc_param(self, name):
        attributes = {}

        self._metadata['name'] = name

        _in = self._metadata.get('_in', 'query')

        if _in not in ('query', 'header', 'path', 'cookie'):
            raise AttributeError('Missing or wrong value of "_in" attribute')
        attributes['in'] = _in

        if not name and not (_in == 'header' and name in ('Accept', 'Content-Type', 'Authorization')):
            raise AttributeError('Missing or wrong value of "name" attribute')
        attributes['name'] = name

        # if 'description' in self._metadata:
        #     attributes['description'] = self._metadata['description']

        if _in == 'path' and not self._required:
            raise AttributeError('Path attributes are always required')

        attributes['required'] = self._required

        # if _in == 'query':
        #     attributes['allowEmptyValue'] = self._metadata.get('allowEmptyValue', False)

        attributes['schema'] = self.openapi_property
        meta = self._metadata

        if isinstance(self, (fields.Nested, fields.Dict)):
            if 'explode' in meta:
                attributes['explode'] = meta['explode']

            if 'style' in meta:
                attributes['style'] = meta['style']

        doc_template = meta.get('doc_template') or None
        if doc_template:
            template = loader.get_template(doc_template)
            description = template.render(self.metadata).strip()

        else:
            description = meta.get('description', self._schema.__doc__) or None

        if description:
            attributes['description'] = markdown2._dedent(description)

        return attributes

    def serialize(self, attr, obj, accessor=None, **kwargs):
        hooks = self._hooks.get(BEFORE_SERIALIZE)
        for hook_name in hooks:
            attr, obj, accessor = getattr(self, hook_name)(attr=attr, obj=obj, accessor=accessor)
        func = getattr(super(), 'serialize')
        value = func(attr, obj, accessor=accessor, **kwargs)
        hooks = self._hooks.get(AFTER_SERIALIZE)
        for hook_name in hooks:
            if value is self._missing:
                continue
            value = getattr(self, hook_name)(value=value)
        return value

    def deserialize(self, value, attr=None, data=None, **kwargs):
        hooks = self._hooks.get(BEFORE_DESERIALIZE)
        for hook_name in hooks:
            if value is self._missing:
                continue
            value, attr, data = getattr(self, hook_name)(value=value, attr=attr, data=data)

        _validate_missing = getattr(self, '_validate_missing', None)

        if _validate_missing:
            _validate_missing(value)

        if value is utils.missing:
            return self._missing

        if self._allow_none is True and value is None:
            return None

        _deserialize = getattr(self, '_deserialize')
        output = _deserialize(value, attr, data, **kwargs)

        hooks = self._hooks.get(AFTER_DESERIALIZE)
        for hook_name in hooks:
            output = getattr(self, hook_name)(output=output)

        _validate = getattr(self, '_validate')
        if _validate:
            _validate(output)
        return output

    # Sample usage of hooks.
    @before_serialize
    def validate_before_serialize(self, attr=None, obj=None, accessor=None):
        return attr, obj, accessor

    @after_serialize
    def validate_after_serialize(self, value=None):
        return value

    @before_deserialize
    def validate_before_deserialize(self, value=None, attr=None, data=None):
        return value, attr, data

    @after_deserialize
    def validate_after_deserialize(self, output=None):
        return output


class Field(ExtendedFieldMixin, fields.Field):
    pass


class Nested(ExtendedFieldMixin, fields.Nested):
    default_error_messages = {
        'type': _('Invalid type.'),
    }

    @property
    def openapi_property(self):
        name = self._metadata.get('name') or getattr(self, 'name', None)
        if not name:
            raise ValueError('Must pass `name` attribute for Nested fields.')
        ret = self._prepare_openapi_property()
        is_unbound_self_referencing = not getattr(self, 'parent', None) and self._nested == 'self'
        if ('ref' in self._metadata) or is_unbound_self_referencing:
            if 'ref' in self._metadata:
                ref_name = self._metadata['ref']
            else:
                ref_name = '#/components/schemas/{name}'.format(name=self._metadata.name)
            ref_schema = {'$ref': ref_name}
            if self._many:
                ret['type'] = 'array'
                ret['items'] = ref_schema
            else:
                if ret:
                    ret.update({'allOf': [ref_schema]})
                else:
                    ret.update(ref_schema)
        else:
            schema_dict = self._schema.doc_schema
            if ret and '$ref' in schema_dict:
                ret.update({'allOf': [schema_dict, ]})
            else:
                ret.update(schema_dict)
        return ret


class List(ExtendedFieldMixin, fields.List):
    default_error_messages = {
        'invalid': _('Not a valid list.'),
    }

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'array'
        ret['items'] = self._container.openapi_property
        return ret


class Dict(ExtendedFieldMixin, fields.Dict):
    default_error_messages = {
        'invalid': _('Not a valid mapping type.'),
    }

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'object'
        ret['nullable'] = self._metadata.get('nullable', False)
        if self._value_container:
            ret['additionalProperties'] = self._value_container.openapi_property
        return ret


class String(ExtendedFieldMixin, fields.String):
    default_error_messages = {
        'invalid': _('Not a valid string.'),
        'invalid_utf8': _('Not a valid utf-8 string.'),
        'invalid_multiple_values': _('Multiple values are not allowed.'),
    }

    @before_deserialize
    def validate_if_not_list(self, value=None, attr=None, data=None):
        if isinstance(value, (list, set)):
            self.fail('invalid_multiple_values')
        return value, attr, data


class Base64String(ExtendedFieldMixin, fields.String):
    default_error_messages = {
        'invalid_base64': 'Invalid data format for base64 encoding.',
        'too_long': 'Too long data.'
    }

    @before_deserialize
    def validate_data(self, value=None, attr=None, data=None):
        data = value.split(';base64,')[-1].encode('utf-8')
        max_size = self.metadata.get('max_size', 0)
        try:
            data = base64.b64decode(data)
        except binascii.Error:
            self.fail(self.base64_error)
        if self.max_size:
            if len(data) > max_size:
                self.fail(self.length_error)
        return value


class UUID(ExtendedFieldMixin, fields.UUID):
    default_error_messages = {
        'invalid_uuid': _('Not a valid UUID.'),
    }

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'string'
        ret['format'] = 'uuid'
        return ret


class Url(ExtendedFieldMixin, fields.Url):
    default_error_messages = {'invalid': _('Not a valid URL.')}

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'string'
        ret['format'] = 'url'
        return ret


class Email(ExtendedFieldMixin, fields.Email):
    default_error_messages = {'invalid': _('Not a valid email address.')}

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'string'
        ret['format'] = 'email'
        return ret


class Integer(ExtendedFieldMixin, fields.Integer):
    default_error_messages = {
        'invalid': _('Not a valid integer.'),
    }

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'integer'
        ret['format'] = 'int32'
        return ret


class Number(ExtendedFieldMixin, fields.Number):
    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'number'
        return ret


class Decimal(ExtendedFieldMixin, fields.Decimal):
    default_error_messages = {
        'special': _('Special numeric values (nan or infinity) are not permitted.'),
    }

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'number'
        return ret


class Float(ExtendedFieldMixin, fields.Float):
    default_error_messages = {
        'special': _('Special numeric values (nan or infinity) are not permitted.'),
    }

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'number'
        ret['format'] = 'float'
        return ret


class Boolean(ExtendedFieldMixin, fields.Boolean):
    default_error_messages = {
        'invalid': _('Not a valid boolean.'),
    }

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'boolean'
        return ret


class Time(ExtendedFieldMixin, fields.Time):
    default_error_messages = {
        'invalid': _('Not a valid time.'),
        'format': _('"{input}" cannot be formatted as a time.'),
    }


class Date(ExtendedFieldMixin, fields.Date):
    default_error_messages = {
        'invalid': _('Not a valid date.'),
        'format': _('"{input}" cannot be formatted as a date.'),
    }

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'string'
        ret['format'] = 'date'
        return ret


class DateTime(ExtendedFieldMixin, fields.DateTime):
    SERIALIZATION_FUNCS = {
        'iso': utils.isoformat,
        'iso8601': utils.isoformat,
        'iso8601T': api_utils.isoformat_with_z,
        'rfc': utils.rfcformat,
        'rfc822': utils.rfcformat,
    }

    DESERIALIZATION_FUNCS = {
        'iso': utils.from_iso_datetime,
        'iso8601': utils.from_iso_datetime,
        'iso8601T': api_utils.from_iso_with_z_datetime,
        'rfc': utils.from_rfc,
        'rfc822': utils.from_rfc,
    }

    DEFAULT_FORMAT = 'iso8601T'

    default_error_messages = {
        'invalid': _('Not a valid {obj_type}.'),
        'format': _('"{input}" cannot be formatted as a {obj_type}.'),
    }

    @property
    def openapi_property(self):
        ret = self._prepare_openapi_property()
        ret['type'] = 'string'
        ret['format'] = 'date-time'
        return ret


class TimeDelta(ExtendedFieldMixin, fields.TimeDelta):
    default_error_messages = {
        'invalid': _('Not a valid period of time.'),
        'format': _('{input!r} cannot be formatted as a timedelta.'),
    }


class Method(ExtendedFieldMixin, fields.Method):
    pass


class Function(ExtendedFieldMixin, fields.Function):
    pass


class Constant(ExtendedFieldMixin, fields.Constant):
    pass


# Aliases
URL = Url
Str = String
Bool = Boolean
Int = Integer
Raw = Field
