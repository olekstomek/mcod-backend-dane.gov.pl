import factory

from mcod.users.factories import UserFactory
from mcod.watchers import models

_WATCHER_TYPES = [i[0] for i in models.WATCHER_TYPES]
_NOTIFICATION_TYPES = [i[0] for i in models.NOTIFICATION_TYPES]
_NOTIFICATION_STATUS_CHOICES = [i[0] for i in models.NOTIFICATION_STATUS_CHOICES]


class WatcherFactory(factory.django.DjangoModelFactory):
    watcher_type = factory.Faker('random_element', elements=_WATCHER_TYPES)
    object_name = factory.Sequence(lambda n: "object_%s" % n)
    object_ident = factory.Sequence(lambda n: "object_id_%s" % n)
    ref_field = 'modified'
    ref_value = factory.Faker('past_date', start_date="-30d")

    class Meta:
        model = models.Watcher


class SubscriptionFactory(factory.django.DjangoModelFactory):
    watcher = factory.SubFactory(WatcherFactory)
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('sentence', nb_words=6)
    enable_notifications = factory.Faker(bool)

    class Meta:
        model = models.Subscription


class NotificationFactory(factory.django.DjangoModelFactory):
    subscription = factory.SubFactory(SubscriptionFactory)
    notification_type = factory.Faker('random_element', elements=_NOTIFICATION_TYPES)
    status = factory.Faker('random_element', elements=_NOTIFICATION_STATUS_CHOICES)
