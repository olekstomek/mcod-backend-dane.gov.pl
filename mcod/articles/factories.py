import factory

from mcod.articles import models
from mcod.core.registries import factories_registry
from mcod.licenses.factories import LicenseFactory


class ArticleCategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('text', max_nb_chars=80, locale='pl_PL')
    description = factory.Faker('paragraph', nb_sentences=5)

    class Meta:
        model = models.ArticleCategory
        django_get_or_create = ('name',)

    @factory.post_generation
    def article_set(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for article in extracted:
                self.article_set.add(article)


class ArticleFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=80, locale='pl_PL')
    notes = factory.Faker('paragraph', nb_sentences=5)
    author = factory.Faker('name')
    views_count = factory.Faker('random_int', min=0, max=500)
    category = factory.SubFactory(ArticleCategoryFactory)
    license = factory.SubFactory(LicenseFactory)
    status = 'published'

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
        django_get_or_create = ('title',)


factories_registry.register('article', ArticleFactory)
factories_registry.register('article category', ArticleCategoryFactory)
