import random

import factory

from mcod.categories.factories import CategoryFactory
from mcod.datasets import models
from mcod.licenses.factories import LicenseFactory
from mcod.organizations.factories import OrganizationFactory

_UPDATE_FREQUENCY = [i[0] for i in models.UPDATE_FREQUENCY]


class DatasetFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=100, locale='pl_PL')
    slug = factory.Faker('slug')
    notes = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='pl_PL')
    url = factory.Faker('url')
    views_count = random.randint(0, 500)
    update_frequency = factory.Faker('random_element', elements=_UPDATE_FREQUENCY)
    category = factory.SubFactory(CategoryFactory)
    license = factory.SubFactory(LicenseFactory)
    organization = factory.SubFactory(OrganizationFactory)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.organizations.add(tag)

    class Meta:
        model = models.Dataset
