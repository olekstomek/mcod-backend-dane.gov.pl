from operator import itemgetter
from urllib.parse import urlsplit, urlunsplit, parse_qsl

from django.apps import apps
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from model_utils.models import TimeStampedModel

from mcod.watchers.signals import watcher_updated, query_watcher_created
from mcod.watchers.tasks import watcher_updated_task, query_watcher_created_task

OBJECT_NAME_TO_MODEL = {
    'application': 'applications.Application',
    'article': 'articles.Article',
    'article_category': 'articles.ArticleCategory',
    'category': 'categories.Category',
    'dataset': 'datasets.Dataset',
    'resource': 'resources.Resource',
    'institution': 'organizations.Organization',
    'tag': 'tags.Tag',
}

STATUS_CHOICES = (
    ('active', _('Active')),
    ('canceled', _('Canceled'))
)

WATCHER_TYPE_MODEL = 'model'
WATCHER_TYPE_SEARCH_QUERY = 'search_query'

WATCHER_TYPES = (
    (WATCHER_TYPE_MODEL, 'Model'),
    (WATCHER_TYPE_SEARCH_QUERY, 'Search query')
)

NOTIFICATION_STATUS_CHOICES = (
    ('new', 'New'),
    ('read', 'Read')
)

NOTIFICATION_TYPES = (
    ('object_restored', 'Object republished'),
    ('object_trashed', 'Object withdrawaled'),
    ('object_updated', 'Object updated'),
    ('related_object_publicated', 'Related object publicated'),
    ('related_object_updated', 'Related object updated'),
    ('related_object_restored', 'Related object republished'),
    ('related_object_trashed', 'Related object withdrawaled'),
    ('result_count_incresed', 'Results incresed'),
    ('result_count_decresed', 'Results decresed'),
)


class InvalidRefField(Exception):
    pass


class InvalidRefValue(Exception):
    pass


class ObjectCannotBeWatched(Exception):
    pass


class UnknownView(Exception):
    pass


class InvalidUrl(Exception):
    pass


class UrlDictError(Exception):
    pass


class Watcher(TimeStampedModel):
    watcher_type = models.CharField(max_length=15, choices=WATCHER_TYPES, null=False, default=WATCHER_TYPE_MODEL)
    object_name = models.CharField(max_length=128, null=False)
    object_ident = models.CharField(max_length=256, null=False)
    ref_field = models.CharField(max_length=64, null=False, default='last_modified')
    ref_value = models.TextField(null=False)
    last_ref_change = models.DateTimeField(null=True)
    tracker = FieldTracker(fields=['ref_value'])

    class Meta:
        indexes = [
            models.Index(fields=['watcher_type', 'object_name', 'object_ident'])
        ]
        constraints = [
            models.UniqueConstraint(fields=['watcher_type', 'object_name', 'object_ident'], name='unique_model_watcher')
        ]

    @cached_property
    def obj(self):
        if self.watcher_type == 'model':
            app_label, model_name = self.object_name.split('.')
            model = apps.get_model(app_label, model_name.title())
            if hasattr(model, 'raw'):
                instance = model.raw.get(pk=self.object_ident)
            else:
                instance = model.objects.get(pk=self.object_ident)
            return instance
        return None


@receiver(pre_save, sender=Watcher)
def lower_object_name(sender, instance, *args, **kwargs):
    instance.object_name = instance.object_name.lower()


class ModelWatcherManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(watcher_type=WATCHER_TYPE_MODEL)

    def create(self, **kwargs):
        return super().create(watcher_type=WATCHER_TYPE_MODEL, **kwargs)

    def create_from_instance(self, instance):
        if not instance.is_watchable:
            raise ObjectCannotBeWatched('Watcher for this object cannot be created.')
        watched_field = getattr(instance, 'watcher_ref_field', 'modified')
        if not hasattr(instance, watched_field):
            raise InvalidRefField('Watcher reference field is invalid.')

        watched_field_value = str(getattr(instance, watched_field))

        object_name = '{}.{}'.format(instance._meta.app_label, instance._meta.object_name)
        return self.create(
            object_name=object_name,
            object_ident=str(instance.id),
            ref_field=watched_field,
            ref_value=watched_field_value,
            last_ref_change=now()
        )

    def update_from_instance(self, instance, obj_state='state_updated', notify_subscribers=True, force=False, **kwargs):
        watcher = self.get_from_instance(instance)
        instance = instance or watcher.obj

        watcher.ref_value = str(getattr(instance, watcher.ref_field))
        changed = force if force else watcher.tracker.has_changed('ref_value')

        if changed:
            prev_value = watcher.tracker.previous('ref_value')

            result = self.update(
                last_ref_change=now(),
                ref_value=watcher.ref_value,
            )
            if notify_subscribers:
                watcher_updated.send(watcher._meta.model, instance=watcher, prev_value=prev_value, obj_state=obj_state)
            return result

        return False

    def get_from_instance(self, instance):
        object_name = '{}.{}'.format(instance._meta.app_label, instance._meta.object_name)

        return self.get(
            object_name=object_name,
            object_ident=str(instance.id)
        )

    def get_or_create_from_instance(self, instance):
        created = False
        try:
            watcher = self.get_from_instance(instance)
        except ModelWatcher.DoesNotExist:
            watcher = self.create_from_instance(instance)
            created = True
        return watcher, created


class ModelWatcher(Watcher):
    objects = ModelWatcherManager()

    class Meta:
        proxy = True


class SearchQueryWatcherManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(watcher_type=WATCHER_TYPE_SEARCH_QUERY)

    def create(self, **kwargs):
        return super().create(watcher_type=WATCHER_TYPE_SEARCH_QUERY, **kwargs)

    @staticmethod
    def _normalize_url(url):
        url_split = urlsplit(url)
        api_split = urlsplit(settings.API_URL)
        if url_split.scheme != api_split.scheme or url_split.netloc != api_split.netloc:
            raise InvalidUrl('Invalid url address.')
        parts = parse_qsl(url_split.query)
        parts.sort(key=itemgetter(0, 1))
        new_query = '&'.join('{}={}'.format(*part) for part in parts)
        url_split = url_split._replace(query=new_query)
        return urlunsplit(url_split)

    def create_from_url(self, url):
        _url = self._normalize_url(url)
        watcher = self.create(
            object_name='query',
            object_ident=_url,
            ref_field='meta.count',
            ref_value=0,
            last_ref_change=now()
        )
        query_watcher_created.send(watcher._meta.model, instance=watcher, created_at=now())

        return watcher

    def update_from_url(self, url, new_value, obj_state='state_updated', notify_subscribers=True, force=False):
        watcher = self.get_from_url(url)

        try:
            new_value = int(new_value)
        except TypeError:
            raise InvalidRefValue('Value must be a number')

        watcher.ref_value = new_value
        changed = force if force else watcher.tracker.has_changed('ref_value')

        if changed:
            prev_value = watcher.tracker.previous('ref_value')

            result = self.update(
                last_ref_change=now(),
                ref_value=watcher.ref_value,
            )
            if notify_subscribers:
                watcher_updated.send(watcher._meta.model, instance=watcher, prev_value=prev_value, obj_state=obj_state)
            return result

        return False

    def get_from_url(self, url):
        url = self._normalize_url(url)

        return self.get(
            object_name='query',
            object_ident=url
        )

    def get_or_create_from_url(self, url):
        created = False
        try:
            watcher = self.get_from_url(url)
        except ModelWatcher.DoesNotExist:
            watcher = self.create_from_url(url)
            created = True
        return watcher, created


class SearchQueryWatcher(Watcher):
    objects = SearchQueryWatcherManager()

    class Meta:
        proxy = True


class SubscriptionManager(models.Manager):
    def __get_instance(self, name, ident):
        app_label, model_name = OBJECT_NAME_TO_MODEL[name].split('.')
        model = apps.get_model(app_label, model_name.title())
        return model.objects.get(pk=ident)

    def create_from_request(self, request):
        data = request.cleaned['data']['attributes']
        _name = data['object_name']
        _ident = data['object_ident']
        if _name == 'query':
            watcher, _ = SearchQueryWatcher.objects.get_or_create_from_url(_ident)
        else:
            instance = self.__get_instance(_name, _ident)
            watcher, _ = ModelWatcher.objects.get_or_create_from_instance(instance)

        name = data.get('name') or '{}-{}'.format(_name, _ident)

        return Subscription.objects.create(
            watcher=watcher,
            user=request.user,
            name=name,
            enable_notifications=data.get('enable_notifications') or True,
            customfields=data.get('customfields') or None,
            reported_till=now()
        )

    def update_from_request(self, id, request):
        data = request.cleaned['data']['attributes']
        Subscription.objects.filter(id=id).update(**data)
        return Subscription.objects.get(pk=id)

    def get_from_request(self, request):
        data = request.cleaned['data']['attributes']
        _name = data['object_name']
        _ident = data['object_ident']
        if _name == 'query':
            watcher = SearchQueryWatcher.objects.get_from_url(_ident)
        else:
            instance = self.__get_instance(_name, _ident)
            watcher = ModelWatcher.objects.get_from_instance(instance)

        return Subscription.objects.get(watcher=watcher, user=request.user)


class Subscription(TimeStampedModel):
    watcher = models.ForeignKey(
        Watcher,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        editable=False,
        related_name='subscriptions'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        editable=False,
        related_name='subscriptions'
    )
    name = models.CharField(max_length=100, null=False, blank=False)
    enable_notifications = models.BooleanField(null=False, default=True)
    customfields = JSONField(null=True)
    reported_till = models.DateTimeField(null=True)

    objects = SubscriptionManager()

    @property
    def display_name(self):
        return self.name or getattr(self.watcher.obj, 'display_name', None) or 'Undefined'

    @property
    def api_url(self):
        if not self.id:
            return None
        return '{}/{}/{}'.format(settings.API_URL, self._meta.app_label, self.id)

    @property
    def object_name(self):
        return self._meta.object_name.lower()


class Notification(TimeStampedModel):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        editable=False,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS_CHOICES)

    @property
    def api_url(self):
        if not self.id:
            return None
        return '{}/{}/{}'.format(settings.API_URL, self._meta.app_label, self.id)

    @property
    def object_name(self):
        return self._meta.object_name.lower()


@receiver(watcher_updated, sender=ModelWatcher)
def send_notifications(instance, prev_value=None, obj_state=None, **kwargs):
    watcher_updated_task.s(instance.id, prev_value, obj_state).apply_async(countdown=1)


@receiver(query_watcher_created, sender=SearchQueryWatcher)
def update_ref_value(instance, created_at=None, **kwargs):
    query_watcher_created_task.s(instance.id, created_at=created_at).apply_async(countdown=1)
