import factory

from mcod.articles import models
from mcod.licenses.factories import LicenseFactory


class ArticleCategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('text', max_nb_chars=80, locale='pl_PL')
    description = factory.Faker('paragraph', nb_sentences=5)

    class Meta:
        model = models.ArticleCategory


class ArticleFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=80, locale='pl_PL')
    notes = factory.Faker('paragraph', nb_sentences=5)
    author = factory.Faker('name')
    category = factory.SubFactory(ArticleCategoryFactory)
    license = factory.SubFactory(LicenseFactory)

    @factory.post_generation
    def datasets(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for dataset in extracted:
                self.datasets.add(dataset)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)

    class Meta:
        model = models.Article
