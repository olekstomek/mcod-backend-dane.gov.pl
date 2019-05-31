import factory

from mcod.organizations import models

_INSTITUTION_TYPES = [i[0] for i in models.INSTITUTION_TYPE_CHOICES]


class OrganizationFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('company', locale='pl_PL')
    description = factory.Faker('paragraph', nb_sentences=5)
    email = factory.Faker('company_email')
    institution_type = 'state'
    slug = factory.Faker('slug')
    image = factory.django.ImageField(color='blue')
    institution_type = factory.Faker('random_element', elements=_INSTITUTION_TYPES)
    postal_code = factory.Faker('postcode', locale='pl_PL')
    city = factory.Faker('city', locale='pl_PL')
    street_type = factory.Faker('street_prefix_short', locale='pl_PL')
    street = factory.Faker('street_name', locale='pl_PL')
    street_number = factory.Faker('building_number', locale='pl_PL')
    email = factory.Faker('email', locale='pl_PL')
    epuap = factory.Faker('uri', locale='pl_PL')
    fax = factory.Faker('phone_number', locale='pl_PL')
    tel = factory.Faker('phone_number', locale='pl_PL')
    regon = factory.Faker('regon', locale='pl_PL')
    website = factory.Faker('url', locale='pl_PL')

    class Meta:
        model = models.Organization
