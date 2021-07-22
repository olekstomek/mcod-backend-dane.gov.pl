import logging

from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from modeltrans.fields import TranslationField

from mcod.core.api.search import signals as search_signals
from mcod.core.api.rdf import signals as rdf_signals
from mcod.core.api.search.tasks import null_field_in_related_task
from mcod.core.db.managers import TrashManager
from mcod.core.db.models import ExtendedModel
from mcod.core.managers import SoftDeletableManager
from mcod.licenses.signals import update_related_datasets, null_in_related_datasets

signal_logger = logging.getLogger('signals')


class License(ExtendedModel):
    SIGNALS_MAP = {
        'updated': (update_related_datasets, rdf_signals.update_related_graph),
        'published': (update_related_datasets, rdf_signals.update_related_graph),
        'restored': (update_related_datasets, rdf_signals.update_related_graph),
        'removed': (null_in_related_datasets, rdf_signals.update_related_graph),
    }
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    title = models.CharField(max_length=250, verbose_name=_('Title'))
    url = models.URLField(blank=True, null=True, verbose_name=_('URL'))

    def __str__(self):
        return self.title

    i18n = TranslationField(fields=("name", "title"))
    objects = SoftDeletableManager()
    trash = TrashManager()
    tracker = FieldTracker()
    slugify_field = 'name'

    @classmethod
    def accusative_case(cls):
        return _("acc: License")

    class Meta:
        verbose_name = _('License')
        verbose_name_plural = _('Licenses')
        default_manager_name = "objects"
        indexes = [GinIndex(fields=["i18n"]), ]


@receiver(null_in_related_datasets, sender=License)
def null_license_in_datasets(sender, instance, *args, **kwargs):
    signal_logger.debug(
        'Setting license to null in related datasets',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'null_in_related_datasets'
        },
        exc_info=1
    )
    null_field_in_related_task.apply_async(
        args=(instance._meta.app_label, instance._meta.object_name, instance.id),
        countdown=2)


@receiver(update_related_datasets, sender=License)
def update_license_in_datasets(sender, instance, *args, **kwargs):
    signal_logger.debug(
        'Updating related datasets',
        extra={
            'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
            'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
            'instance_id': instance.id,
            'signal': 'update_related_datasets'
        },
        exc_info=1
    )
    for dataset in instance.dataset_set.all():
        search_signals.update_document.send(dataset._meta.model, dataset)
