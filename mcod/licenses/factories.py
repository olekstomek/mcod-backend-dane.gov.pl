import factory

from mcod.licenses import models


class LicenseFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word', locale='pl_PL')
    title = factory.Faker('text', max_nb_chars=50, locale='pl_PL')
    url = factory.Faker('url')

    class Meta:
        model = models.License
