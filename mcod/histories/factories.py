import factory

from mcod.core.registries import factories_registry
from mcod.histories.models import History


class HistoryFactory(factory.django.DjangoModelFactory):
    change_user_id = 999
    row_id = 9999
    table_name = factory.Faker(
        'random_element',
        elements=['application', 'application_tag', 'article_tag', 'article', 'dataset', 'dataset_tag', 'organization',
                  'resource', 'user', 'user_organization'])
    action = factory.Faker('random_element', elements=['DELETE', 'INSERT', 'UPDATE'])
    message = factory.Faker("text", max_nb_chars=100, locale="pl_PL")

    class Meta:
        model = History


factories_registry.register('history', HistoryFactory)
