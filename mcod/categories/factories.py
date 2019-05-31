import factory

from mcod.categories import models


class CategoryFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=30, locale='pl_PL')
    description = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='pl_PL')

    class Meta:
        model = models.Category
