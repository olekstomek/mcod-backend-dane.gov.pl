import factory

from mcod.core.registries import factories_registry
from mcod.special_signs.models import SpecialSign


class SpecialSignFactory(factory.django.DjangoModelFactory):
    symbol = factory.Faker('random_element', elements=('@', '#', '%', '.', '*'))
    name = factory.Faker('text', max_nb_chars=15, locale='pl_PL')
    description = factory.Faker('paragraph', nb_sentences=5)

    class Meta:
        model = SpecialSign


factories_registry.register('specialsign', SpecialSign)
