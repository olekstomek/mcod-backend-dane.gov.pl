import logging

from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from model_utils.managers import SoftDeletableManager
from modeltrans.fields import TranslationField

from mcod.applications.signals import generate_thumbnail
from mcod.applications.tasks import generate_logo_thumbnail_task
from mcod.core import signals as core_signals, storages
from mcod.core.api.search import signals as search_signals
from mcod.core.db.managers import DeletedManager
from mcod.core.db.models import ExtendedModel, update_watcher

User = get_user_model()

signal_logger = logging.getLogger('signals')


class Application(ExtendedModel):
    SIGNALS_MAP = {
        'updated': (generate_thumbnail, core_signals.notify_updated),
        'published': (generate_thumbnail, core_signals.notify_published),
        'restored': (generate_thumbnail, core_signals.notify_restored),
        'removed': (search_signals.remove_document, core_signals.notify_removed),
        'm2m_added': (search_signals.update_document, core_signals.notify_m2m_added,),
        'm2m_removed': (search_signals.update_document, core_signals.notify_m2m_removed,),
        'm2m_cleaned': (search_signals.update_document, core_signals.notify_m2m_cleaned,),
    }
    title = models.CharField(max_length=300, verbose_name=_("Title"))
    notes = models.TextField(verbose_name=_("Notes"), null=True)
    author = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Author"))
    url = models.URLField(max_length=300, verbose_name=_("App URL"), null=True)
    image = models.ImageField(
        max_length=200, storage=storages.get_storage('applications'),
        upload_to='%Y%m%d', blank=True, null=True, verbose_name=_("Image URL")
    )
    image_thumb = models.ImageField(
        storage=storages.get_storage('applications'),
        upload_to='%Y%m%d', blank=True, null=True
    )

    datasets = models.ManyToManyField('datasets.Dataset',
                                      db_table='application_dataset',
                                      verbose_name=_('Datasets'),
                                      related_name='applications',
                                      related_query_name="application")
    tags = models.ManyToManyField('tags.Tag',
                                  blank=True,
                                  db_table='application_tag',
                                  verbose_name=_('Tag'),
                                  related_name='applications',
                                  related_query_name="application")

    created_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Created by"),
        related_name='applications_created'
    )

    modified_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        blank=False,
        editable=False,
        null=True,
        verbose_name=_("Modified by"),
        related_name='applications_modified'
    )

    @cached_property
    def image_url(self):
        try:
            return self.image.url
        except ValueError:
            return ''

    @cached_property
    def image_thumb_url(self):
        try:
            return self.image_thumb.url
        except ValueError:
            return ''

    @cached_property
    def tags_list(self):
        return [tag.name_translated for tag in self.tags.all()]

    @cached_property
    def users_following_list(self):
        return [user.id for user in self.users_following.all()]

    def __str__(self):
        return self.title

    @classmethod
    def accusative_case(cls):
        return _("acc: Application")

    def published_datasets(self):
        return self.datasets.filter(status='published')

    i18n = TranslationField(fields=("title", "notes"))
    raw = models.Manager()
    objects = SoftDeletableManager()
    deleted = DeletedManager()
    tracker = FieldTracker()
    slugify_field = 'title'

    class Meta:
        verbose_name = _("Application")
        verbose_name_plural = _("Applications")
        db_table = "application"
        default_manager_name = "objects"
        indexes = [GinIndex(fields=["i18n"]), ]


@receiver(generate_thumbnail, sender=Application)
def regenerate_thumbnail(sender, instance, *args, **kwargs):
    signal_logger.info(
        'Regenerating thumbnail ',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'generate_thumbnail'
        },
        exc_info=1
    )
    if instance.tracker.has_changed('image'):
        generate_logo_thumbnail_task.delay(instance.id)
    else:
        search_signals.update_document.send(sender, instance)


class ApplicationTrash(Application):
    class Meta:
        proxy = True
        verbose_name = _("Trash")
        verbose_name_plural = _("Trash")


core_signals.notify_published.connect(update_watcher, sender=Application)
core_signals.notify_restored.connect(update_watcher, sender=Application)
core_signals.notify_updated.connect(update_watcher, sender=Application)
core_signals.notify_removed.connect(update_watcher, sender=Application)

core_signals.notify_published.connect(update_watcher, sender=ApplicationTrash)
core_signals.notify_restored.connect(update_watcher, sender=ApplicationTrash)
core_signals.notify_updated.connect(update_watcher, sender=ApplicationTrash)
core_signals.notify_removed.connect(update_watcher, sender=ApplicationTrash)
