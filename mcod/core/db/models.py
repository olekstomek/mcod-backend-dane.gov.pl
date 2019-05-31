import logging
import uuid
from functools import partial

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from model_utils import Choices
from model_utils.models import SoftDeletableModel, TimeStampedModel
from model_utils.models import StatusModel, MonitorField

from mcod.core import signals
from mcod.core.api.jsonapi.serializers import Object
from mcod.core.api.jsonapi.serializers import object_attrs_registry as oar
from mcod.core.api.search import signals as search_signals
from mcod.core.serializers import csv_serializers_registry as csr

signal_logger = logging.getLogger('signals')

STATUS_CHOICES = [
    ('published', _('Published')),
    ('draft', _('Draft')),
]

_SIGNALS_MAP = {
    'updated': (search_signals.update_document_with_related, signals.notify_updated),
    'published': (search_signals.update_document_with_related, signals.notify_published),
    'restored': (search_signals.update_document_with_related, signals.notify_restored),
    'removed': (search_signals.remove_document_with_related, signals.notify_removed),
    'm2m_added': (search_signals.update_document_related, signals.notify_m2m_added,),
    'm2m_removed': (search_signals.update_document_related, signals.notify_m2m_removed,),
    'm2m_cleaned': (search_signals.update_document_related, signals.notify_m2m_cleaned,),
    'unsupported': []
}


def default_slug_value():
    return uuid.uuid4().hex


class ExtendedModel(StatusModel, SoftDeletableModel, TimeStampedModel):
    STATUS = Choices(*STATUS_CHOICES)
    slug = models.SlugField(max_length=600, null=False, blank=True, default=uuid.uuid4)
    uuid = models.UUIDField(default=uuid.uuid4)

    removed_at = MonitorField(monitor='is_removed', when=[True, ])
    published_at = MonitorField(monitor='status', when=['published', ])

    views_count = models.PositiveIntegerField(default=0)

    def _get_translated_field_dict(self, field_name):
        _i18n = self._meta.get_field('i18n')
        if field_name not in _i18n.fields:
            raise ValueError(f'Field {field_name} does not support translations.')
        return {
            _lang: getattr(self, f'{field_name}_{_lang}') or getattr(self, f'{field_name}_i18n')
            for _lang in settings.MODELTRANS_AVAILABLE_LANGUAGES
        }

    @property
    def object_name(self):
        return self._meta.object_name.lower()

    @property
    def ident(self):
        return '{},{}'.format(self.id, self.slug) if self.slug else id

    @property
    def api_url(self):
        if not self.id:
            return None

        return '{}/{}/{}'.format(settings.API_URL, self._meta.app_label, self.ident)

    @property
    def display_name(self):
        if self.id:
            return '{}-{}'.format(self._meta.object_name.lower(), self.id)
        return None

    def to_jsonapi(self, _schema=None):
        _schema = _schema or oar.get_serializer(self)
        data_cls = type(
            '{}Data'.format(self.__class__.__name__),
            (Object,), {}
        )
        setattr(data_cls.opts, 'attrs_schema', _schema)
        return data_cls(many=False).dump(self)

    def to_csv(self, _schema=None):
        _schema = _schema or csr.get_serializer(self)
        return _schema(many=False).dump(self)

    @property
    def signals_map(self):
        _map = dict(_SIGNALS_MAP)
        _map.update(getattr(self, 'SIGNALS_MAP', {}))
        return _map

    @property
    def is_indexable(self):
        return True

    @property
    def is_watchable(self):
        return True

    @cached_property
    def users_following_list(self):
        # TODO: refactor this to new mechanism
        return [user.id for user in self.users_following.all()]

    @property
    def is_created(self):
        return True if not self._get_pk_val(self._meta) else False

    @property
    def was_removed(self):
        return True if self.tracker.previous('is_removed') else False

    @property
    def prev_status(self):
        return self.tracker.previous('status')

    @property
    def was_published(self):
        return True if self.tracker.previous('published_at') else False

    @property
    def state_published(self):
        if all([
            self.status == self.STATUS.published,
            not self.is_removed,
        ]):
            if self.is_created:
                return True
            else:
                if not self.was_published:
                    if self.was_removed:
                        return True
                    else:
                        if self.prev_status in (None, self.STATUS.draft):
                            return True
        return False

    @property
    def state_removed(self):
        if all([
            not self.is_created,
            not self.was_removed,
            self.prev_status == self.STATUS.published
        ]):
            if self.status == self.STATUS.draft:
                return True
            elif self.status == self.STATUS.published and self.is_removed:
                return True
        return False

    @property
    def state_restored(self):
        if all([
            self.status == self.STATUS.published,
            not self.is_removed,
            not self.is_created,
            self.was_published
        ]):
            if self.was_removed:
                return True
            elif self.prev_status == self.STATUS.draft:
                return True
        return False

    @property
    def state_updated(self):
        if all([
            self.status == self.STATUS.published,
            not self.is_removed,
            not self.is_created,
            self.prev_status == self.STATUS.published,
            not self.was_removed
        ]):
            return True
        return False

    def get_state(self):
        for state in self.signals_map:
            result = getattr(self, 'state_{}'.format(state), None)
            if result:
                return state

        return None

    def get_unique_slug(self):
        field_name = getattr(self, 'slugify_field', 'title')
        value = getattr(self, field_name)
        if value:
            origin_slug = slugify(value)
            unique_slug = origin_slug
            c = 1
            qs = self._meta.model.objects.filter(slug=unique_slug)
            if not self.is_created and unique_slug:
                qs = qs.exclude(pk=self.pk)
            while qs.exists():
                unique_slug = '%s-%d' % (origin_slug, c)
                c += 1
            value = unique_slug
        else:
            value = str(uuid.uuid4())
        return value

    @staticmethod
    def on_class_prepared(sender, *args, **kwargs):
        def prop_func(self, field_name):
            obj = type(
                '{}_translated'.format(field_name),
                (object,),
                self._get_translated_field_dict(field_name))
            return obj()

        if not issubclass(sender, ExtendedModel) or sender._meta.proxy:
            return

        _i18n = sender._meta.get_field('i18n')
        if 'slug' not in _i18n.fields:
            fields = list(_i18n.fields)
            fields.append('slug')
            _i18n.fields = tuple(fields)

        for field_name in _i18n.fields:
            setattr(
                sender,
                '{}_translated'.format(field_name),
                property(partial(prop_func, field_name=field_name)))

    @staticmethod
    def on_pre_init(sender, *args, **kwargs):
        pass

    @staticmethod
    def on_post_init(sender, instance, **kwargs):
        pass

    @staticmethod
    def on_pre_save(sender, instance, raw, using, update_fields, **kwargs):
        if not instance.slug:
            field_name = getattr(instance, 'slugify_field', 'title')
            value = getattr(instance, field_name)
            instance.slug = slugify(value) if value else instance.get_unique_slug()

    @staticmethod
    def on_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
        state = instance.get_state()
        if state:
            for _signal in instance.signals_map[state]:
                _signal.send(sender, instance, state=state)

    @staticmethod
    def on_pre_delete(sender, instance, using, **kwargs):
        state = instance.get_state()
        if state:
            for _signal in instance.signals_map[state]:
                _signal.send(sender, instance)

    @staticmethod
    def on_post_delete(sender, instance, using, **kwargs):
        pass

    @staticmethod
    def on_m2m_changed(sender, instance, action, reverse, model, pk_set, using, **kwargs):
        if action == "pre_add":
            state = 'm2m_added'
        elif action == "pre_remove":
            state = 'm2m_removed'
        elif action == "pre_clean":
            state = 'm2m_cleaned'
        else:
            # Unsupported signals like post_add, post_remove etc..
            state = 'unsupported'

        for _signal in instance.signals_map[state]:
            _signal.send(sender, instance, model, pk_set)

    class Meta:
        abstract = True


models.signals.class_prepared.connect(ExtendedModel.on_class_prepared)


def update_watcher(sender, instance, *args, state=None, **kwargs):
    signal_logger.info(
        '{} {}'.format(sender._meta.object_name, state),
        extra={
            'sender': '{}.{}'.format(sender._meta.app_label, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.app_label, instance._meta.object_name),
            'instance_id': instance.id,
            'state': state,
            'signal': 'notify_{}'.format(state)
        },
        exc_info=1
    )
    # update_model_watcher_task.apply_async(
    #     args=(instance._meta.app_label, instance._meta.object_name, instance.id, state),
    #     countdown=5
    # )
