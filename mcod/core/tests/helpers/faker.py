# -*- coding: utf-8 -*-
from marshmallow import fields as f
from faker import Faker
from mcod import settings


class FakerSchema(object):
    def __init__(self, faker=None, locale=None, providers=None, includes=None):
        self._faker = faker or Faker(locale=locale, providers=providers, includes=includes)

    def userstate(self):
        return self._faker.sentence(settings.USER_STATE_LIST)

    def get_faker_type(self, _type):
        if hasattr(self, _type):
            return self._type()
        else:
            return getattr(self._faker, _type)()

    def generate_fake(self, schema, runs=1, child_runs=5):
        schema = schema()
        result = [self._generate_single_fake(schema, runs=child_runs) for _ in range(runs)]
        return result[0] if len(result) == 1 else result

    def _generate_single_fake(self, schema, root=None, runs=5):
        data = {}
        fields = filter(lambda i: 'faker_type' in i.metadata, schema.fields.values())
        for field in fields:
            # field_name = field.data_key or field.name
            field_name = field.name
            if hasattr(field, 'nested'):
                root = root if root else field.root
                if field.many:
                    data[field.name] = [self._generate_single_fake(field.schema, root=root, runs=runs) for v in
                                        range(5)]
                else:
                    data[field_name] = self._generate_single_fake(field.schema, root=root, runs=runs)
            else:
                if isinstance(field, f.List):
                    if hasattr(field, 'container') and not isinstance(field.container, f.Dict):
                        data[field_name] = [self.get_faker_type(field.metadata['faker_type']) for v in range(10)]
                    else:
                        data[field_name] = []
                elif isinstance(field, f.Dict):
                    data[field_name] = {}
                else:
                    data[field_name] = self.get_faker_type(field.metadata['faker_type'])
        return data
