import factory

from mcod.tags import models


class TagFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word', locale='pl_PL')
    status = 'published'

    class Meta:
        model = models.Tag
