import factory

from mcod.categories.factories import CategoryFactory
from mcod.core.registries import factories_registry
from mcod.datasets import models
from mcod.licenses.factories import LicenseFactory
from mcod.organizations.factories import OrganizationFactory

_UPDATE_FREQUENCY = [i[0] for i in models.UPDATE_FREQUENCY]


class DatasetFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=100, locale='pl_PL')
    slug = factory.Faker('slug')
    notes = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='pl_PL')
    url = factory.Faker('url')
    views_count = factory.Faker('random_int', min=0, max=500)
    update_frequency = factory.Faker('random_element', elements=_UPDATE_FREQUENCY)
    category = factory.SubFactory(CategoryFactory)
    license = factory.SubFactory(LicenseFactory)
    organization = factory.SubFactory(OrganizationFactory)
    image = factory.Faker('file_name', extension='png')

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)

    @factory.post_generation
    def articles(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for item in extracted:
                self.articles.add(item)

    @factory.post_generation
    def applications(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for dataset in extracted:
                self.applications.add(dataset)

    @factory.post_generation
    def resources(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for resource in extracted:
                self.resources.add(resource)

    @factory.post_generation
    def showcases(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for showcase in extracted:
                self.showcases.add(showcase)

    class Meta:
        model = models.Dataset
        django_get_or_create = ('title',)


factories_registry.register('dataset', DatasetFactory)
