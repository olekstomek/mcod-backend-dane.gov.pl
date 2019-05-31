import factory
from django.utils.text import slugify
from faker import Faker

from mcod.users import models

fake = Faker('pl_PL')


class UserFactory(factory.django.DjangoModelFactory):
    fullname = factory.Faker('name')
    email = factory.LazyAttribute(
        lambda o: slugify(o.fullname) + "@" + fake.free_email_domain())
    password = factory.Faker('password', length=16, special_chars=True, digits=True, upper_case=True, lower_case=True)
    is_staff = False
    is_superuser = False
    state = 'active'

    class Meta:
        model = models.User
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
