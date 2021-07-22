import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from mcod.core.api.search import signals as search_signals
from mcod.harvester.models import DataSource


signal_logger = logging.getLogger('signals')


@receiver(pre_save, sender=DataSource)
def update_last_activation_date(sender, instance, *args, **kwargs):
    if not instance.source_type:
        instance.source_type = DataSource.SOURCE_TYPE_CHOICES[0][0]
    if instance.tracker.has_changed('status') and instance.status == 'active':
        instance.last_activation_date = timezone.now()


@receiver(post_save, sender=DataSource)
def data_source_post_save_callback(sender, instance, *args, **kwargs):
    if any([instance.tracker.has_changed('name'),
            instance.tracker.has_changed('portal_url'),
            instance.tracker.has_changed('source_type')]):  # reindex DatasetsDoc if needed.
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
        for dataset in instance.datasource_datasets.all():
            search_signals.update_document.send(dataset._meta.model, dataset)
