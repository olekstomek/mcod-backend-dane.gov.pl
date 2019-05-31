import logging

from django_elasticsearch_dsl.signals import BaseSignalProcessor

from mcod.core.api.search.tasks import delete_document_task, delete_related_documents_task, delete_with_related_task, \
    update_with_related_task, update_document_task, update_related_task
from mcod.core.signals import ExtendedSignal

signal_logger = logging.getLogger('signals')

update_document = ExtendedSignal()
update_document_with_related = ExtendedSignal()
update_document_related = ExtendedSignal()
remove_document = ExtendedSignal()
remove_document_with_related = ExtendedSignal()


class AsyncSignalProcessor(BaseSignalProcessor):
    def _get_object_name(self, obj):
        return obj._meta.concrete_model._meta.object_name

    def setup(self):
        update_document.connect(self.update)
        update_document_with_related.connect(self.update_with_related)
        update_document_related.connect(self.update_related)
        remove_document.connect(self.remove)
        remove_document_with_related.connect(self.remove_with_related)

    def teardown(self):
        update_document.disconnect(self.update)
        update_document_with_related.disconnect(self.update_with_related)
        update_document_related.disconnect(self.update_related)
        remove_document.disconnect(self.remove)
        remove_document_with_related.disconnect(self.remove_with_related)

    def update(self, sender, instance, *args, **kwargs):
        signal_logger.info(
            'Updating document in elasticsearch',
            extra={
                'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
                'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
                'instance_id': instance.id,
                'signal': 'update_document'
            },
            exc_info=1
        )
        obj_name = self._get_object_name(instance)
        update_document_task.s(instance._meta.app_label, obj_name, instance.id).apply_async(countdown=1)

    def update_related(self, sender, instance, model, pk_set, **kwargs):
        signal_logger.info(
            'Updating related documents in elasticsearch',
            extra={
                'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
                'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
                'instance_id': instance.id,
                'signal': 'update_related'
            },
            exc_info=1
        )

        update_related_task.s(model._meta.app_label, model._meta.object_name, list(pk_set)).apply_async(countdown=2)

    def update_with_related(self, sender, instance, *args, **kwargs):
        signal_logger.info(
            'Updating document and related documents in elasticsearch',
            extra={
                'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
                'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
                'instance_id': instance.id,
                'signal': 'update_document_with_related'
            },
            exc_info=1
        )
        obj_name = self._get_object_name(instance)
        update_with_related_task.s(instance._meta.app_label, obj_name, instance.id).apply_async(countdown=3)

    def remove(self, sender, instance, *args, **kwargs):
        signal_logger.info(
            'Removing document from elasticsearch',
            extra={
                'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
                'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
                'instance_id': instance.id,
                'signal': 'remove_document'
            },
            exc_info=1
        )

        obj_name = self._get_object_name(instance)
        delete_document_task.s(instance._meta.app_label, obj_name, instance.id).apply_async(countdown=1)

    def remove_with_related(self, sender, instance, *args, **kwargs):
        signal_logger.info(
            'Removing document and related documents from elasticsearch',
            extra={
                'sender': '{}.{}'.format(sender._meta.model_name, sender._meta.object_name),
                'instance': '{}.{}'.format(instance._meta.model_name, instance._meta.object_name),
                'instance_id': instance.id,
                'signal': 'remove_document_with_related'
            },
            exc_info=1
        )
        obj_name = self._get_object_name(instance)
        delete_with_related_task.s(instance._meta.app_label, obj_name, instance.id).apply_async(countdown=3)

    def handle_updated(self, sender, instance, **kwargs):
        is_indexable = getattr(instance, 'is_indexable', False)
        if is_indexable:
            should_delete = (hasattr(instance, 'is_removed') and instance.is_removed) or (
                    hasattr(instance, 'status') and instance.status != 'published') or \
                            kwargs.get('qs_delete', False)
            object_name = instance._meta.concrete_model._meta.object_name
            if should_delete:
                delete_with_related_task.s(instance._meta.app_label, object_name, instance.id).apply_async(countdown=3)
            else:
                update_with_related_task.s(instance._meta.app_label, object_name, instance.id).apply_async(countdown=3)

    def handle_pre_delete(self, sender, instance, **kwargs):
        is_indexable = getattr(instance, 'is_indexable', False)
        if is_indexable:
            object_name = instance._meta.concrete_model._meta.object_name
            delete_related_documents_task.s(instance._meta.app_label, object_name, instance.id).apply_async(countdown=1)
            # delete_related_documents_task.apply_async(
            #     args=(instance._meta.app_label, object_name, instance.id),
            #     countdown=2)

    def handle_delete(self, sender, instance, **kwargs):
        is_indexable = getattr(instance, 'is_indexable', False)
        if is_indexable:
            object_name = instance._meta.concrete_model._meta.object_name
            delete_document_task.s(instance._meta.app_label, object_name, instance.id).apply_async(countdown=1)
            # delete_document_task.apply_async(args=(instance._meta.app_label, object_name, instance.id),
            #                                  countdown=2)

    def handle_m2m_changed(self, sender, instance, action, **kwargs):
        if action in ('post_add', 'post_remove', 'post_clear'):
            self.handle_save(sender, instance)
        elif action in ('pre_remove', 'pre_clear'):
            self.handle_pre_delete(sender, instance)
