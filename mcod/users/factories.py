import factory
from django.utils.text import slugify
from faker import Faker

from mcod.core.registries import factories_registry
from mcod.users import models

fake = Faker('pl_PL')


class UserFactory(factory.django.DjangoModelFactory):
    fullname = factory.Faker('name')
    phone = factory.Faker('msisdn')
    email = factory.LazyAttribute(
        lambda o: slugify(o.fullname) + "@" + fake.free_email_domain())
    password = factory.Faker('password', length=16, special_chars=True, digits=True, upper_case=True, lower_case=True)

    is_staff = False
    is_superuser = False
    is_official = False
    state = 'active'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)

    @factory.post_generation
    def organizations(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for org in extracted:
                self.organizations.add(org)

    class Meta:
        model = models.User
        django_get_or_create = ('email',)


class AdminFactory(UserFactory):
    is_staff = True
    is_superuser = True


class AcademyAdminFactory(UserFactory):
    is_staff = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user = super()._create(model_class, *args, **kwargs)
        user.set_academy_perms(is_academy_admin=True)
        return user


class LaboratoryAdminFactory(AdminFactory):
    is_staff = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user = super()._create(model_class, *args, **kwargs)
        user.set_labs_perms(is_labs_admin=True)
        return user


class EditorFactory(UserFactory):
    is_staff = True
    is_superuser = False


class OfficialUserFactory(UserFactory):
    is_official = True


class AgentFactory(UserFactory):
    is_agent = True


class PendingUserFactory(UserFactory):
    state = 'pending'


class InactiveUserFactory(UserFactory):
    is_active = False


class BlockedUserFactory(UserFactory):
    state = 'blocked'


class UnconfirmedUserFactory(UserFactory):
    state = 'active'
    is_active = False


factories_registry.register('active user', UserFactory)
factories_registry.register('pending user', PendingUserFactory)
factories_registry.register('inactive user', InactiveUserFactory)
factories_registry.register('unconfirmed user', UnconfirmedUserFactory)
factories_registry.register('blocked user', BlockedUserFactory)
factories_registry.register('admin user', AdminFactory)
factories_registry.register('editor user', EditorFactory)
factories_registry.register('official user', OfficialUserFactory)
factories_registry.register('agent user', AgentFactory)
factories_registry.register('academy admin', AcademyAdminFactory)
factories_registry.register('laboratory admin', LaboratoryAdminFactory)
