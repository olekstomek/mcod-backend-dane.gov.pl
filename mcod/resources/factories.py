import random
import uuid

import factory

from mcod.datasets.factories import DatasetFactory
from mcod.resources import models

_SUPPORTED_FORMATS = [i[0] for i in models.supported_formats_choices()]
_RESOURCE_TYPES = [i[0] for i in models.RESOURCE_TYPE]


class ResourceFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=100, locale='pl_PL')
    description = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='pl_PL')
    views_count = random.randint(0, 500)
    downloads_count = random.randint(0, 500)
    file = factory.django.FileField(filename='{}.csv'.format(str(uuid.uuid4())))
    link = factory.LazyAttribute(lambda obj: 'http://falconframework.org/media/resources/{}'.format(obj.file.name))
    dataset = factory.SubFactory(DatasetFactory)
    format = factory.Faker('random_element', elements=_SUPPORTED_FORMATS)
    type = factory.Faker('random_element', elements=_RESOURCE_TYPES)
    openness_score = random.randint(1, 5)

    class Meta:
        model = models.Resource
