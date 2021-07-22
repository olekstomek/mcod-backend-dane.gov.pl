import factory

from mcod.harvester.models import DataSource, FREQUENCY_CHOICES
from mcod.core.registries import factories_registry
from mcod.categories.factories import CategoryFactory
from mcod.users.factories import AdminFactory
from mcod.organizations.factories import OrganizationFactory
from mcod.organizations.models import Organization


class DataSourceFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('text', max_nb_chars=80, locale='pl_PL')
    description = factory.Faker('paragraph', nb_sentences=5, locale='pl_PL')
    frequency_in_days = factory.Faker('random_element', elements=[x[0] for x in FREQUENCY_CHOICES])
    status = factory.Faker('random_element', elements=[x[0] for x in DataSource.STATUS_CHOICES])
    license_condition_db_or_copyrighted = factory.Faker('text', max_nb_chars=300, locale='pl_PL')
    institution_type = factory.Faker('random_element', elements=[x[0] for x in Organization.INSTITUTION_TYPE_CHOICES])
    source_type = factory.Faker('random_element', elements=[x[0] for x in DataSource.SOURCE_TYPE_CHOICES])
    created_by = factory.SubFactory(AdminFactory)

    class Meta:
        model = DataSource


class CKANDataSourceFactory(DataSourceFactory):
    source_type = 'ckan'
    portal_url = factory.Faker('url')
    api_url = factory.Faker('url')
    category = factory.SubFactory(CategoryFactory)


class XMLDataSourceFactory(DataSourceFactory):
    source_type = 'xml'
    xml_url = factory.Faker('url')
    organization = factory.SubFactory(OrganizationFactory)


factories_registry.register('datasource', DataSourceFactory)
factories_registry.register('ckan_datasource', CKANDataSourceFactory)
factories_registry.register('xml_datasource', XMLDataSourceFactory)
