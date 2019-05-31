import random
import uuid
from urllib.parse import quote

import factory
from django.utils.text import slugify
from faker import Faker

from mcod.categories import models as cat_models
from mcod.datasets import models as dat_models
from mcod.licenses import models as lic_models
from mcod.organizations import models as org_models
from mcod.resources import models as res_models
from mcod.searchhistories import models as sh_models
from mcod.tags import models as tag_models
from mcod.users import models as usr_models

fake = Faker('pl_PL')


class OrganizationFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('company', locale='pl_PL')
    description = factory.Faker('paragraph', nb_sentences=5)
    email = factory.Faker('company_email')
    institution_type = 'state'
    slug = factory.Faker('slug')
    image = factory.django.ImageField(color='blue')

    class Meta:
        model = org_models.Organization


class UserFactory(factory.django.DjangoModelFactory):
    fullname = factory.Faker('name')
    email = factory.LazyAttribute(
        lambda o: slugify(o.fullname) + "@" + fake.free_email_domain())
    password = factory.Faker('password', length=16, special_chars=True, digits=True, upper_case=True, lower_case=True)
    is_staff = False
    is_superuser = False
    state = 'active'

    class Meta:
        model = usr_models.User
        django_get_or_create = ('email',)


class AdminFactory(UserFactory):
    is_staff = True
    is_superuser = True


class EditorFactory(UserFactory):
    is_staff = True
    is_superuser = False

    @factory.post_generation
    def organizations(self, create, data, **kwargs):
        if not create:
            return

        if data:
            for organization in data:
                self.organizations.add(organization)


class TagFactory(factory.Factory):
    name = factory.Faker('word', locale='pl_PL')
    status = 'published'

    class Meta:
        model = tag_models.Tag


class CategoryFactory(factory.Factory):
    title = factory.Faker('text', max_nb_chars=30, locale='pl_PL')
    # title_en = factory.Faker('text', max_nb_chars=30, locale='en_US')
    description = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='pl_PL')
    # description_en = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='en_US')
    status = 'published'

    class Meta:
        model = cat_models.Category


class LicenseFactory(factory.Factory):
    name = factory.Faker('word', locale='pl_PL')
    title = factory.Faker('text', max_nb_chars=50, locale='pl_PL')
    # title_en = factory.Faker('text', max_nb_chars=50, locale='en_US')
    url = factory.Faker('url')

    class Meta:
        model = lic_models.License


class DatasetFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=100, locale='pl_PL')
    # title_en = factory.Faker('text', max_nb_chars=100, locale='en_US')
    slug = factory.Faker('slug')
    notes = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='pl_PL')
    # notes_en = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='en_US')
    url = factory.Faker('url')
    views_count = random.randint(0, 500)
    update_frequency = 'yearly'
    category = factory.SubFactory(CategoryFactory)
    license = factory.SubFactory(LicenseFactory)
    organization = factory.SubFactory(OrganizationFactory)
    status = 'published'
    is_removed = False

    @factory.post_generation
    def tags(self, create, data, **kwargs):
        if not create:
            return

        if data:
            for tag in data:
                self.organizations.add(tag)

    class Meta:
        model = dat_models.Dataset


class ResourceFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=100, locale='pl_PL')
    # title_en = factory.Faker('text', max_nb_chars=100, locale='en_US')
    description = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='pl_PL')
    # description_en = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='en_US')
    format = 'csv'
    openness_score = 3
    views_count = random.randint(0, 500)
    downloads_count = random.randint(0, 500)
    file = factory.django.FileField(filename='{}.csv'.format(str(uuid.uuid4())))
    dataset = factory.SubFactory(DatasetFactory)
    link = factory.LazyAttribute(lambda obj: 'http://falconframework.org/media/resources/{}'.format(obj.file.name))

    class Meta:
        model = res_models.Resource


class SearchHistoryFactory(factory.django.DjangoModelFactory):
    query_sentence = factory.Faker("text", max_nb_chars=100, locale="pl_PL")
    url = factory.LazyAttribute(lambda obj: f'http://test.dane.gov.pl/datasets?q={quote(obj.query_sentence)}')
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = sh_models.SearchHistory
