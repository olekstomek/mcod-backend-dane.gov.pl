import factory

from mcod.applications import models
from mcod.core.registries import factories_registry


class ApplicationFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=80, locale='pl_PL')
    title_en = factory.Faker('text', max_nb_chars=80)
    notes = factory.Faker('paragraph', nb_sentences=5, locale='pl_PL')
    author = factory.Faker('name')
    url = factory.Faker('url')
    views_count = factory.Faker('random_int', min=0, max=500)
    image = factory.django.ImageField(color='blue')

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
        model = models.Application
        django_get_or_create = ('title',)


class ApplicationProposalFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=80, locale='pl_PL')
    notes = factory.Faker('paragraph', nb_sentences=5, locale='pl_PL')
    author = factory.Faker('name')
    url = factory.Faker('url')

    class Meta:
        model = models.ApplicationProposal
        django_get_or_create = ('title',)


factories_registry.register('application', ApplicationFactory)
factories_registry.register('applicationproposal', ApplicationProposalFactory)
