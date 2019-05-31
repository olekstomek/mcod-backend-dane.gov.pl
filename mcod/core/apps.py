from django.apps import AppConfig


class ExtendedAppMixin:
    def connect_core_signals(self, sender):
        from django.db import models
        from mcod.core.db.models import ExtendedModel
        if issubclass(sender, ExtendedModel):
            models.signals.pre_init.connect(ExtendedModel.on_pre_init, sender=sender)
            models.signals.post_init.connect(ExtendedModel.on_post_init, sender=sender)
            models.signals.pre_save.connect(ExtendedModel.on_pre_save, sender=sender)
            models.signals.post_save.connect(ExtendedModel.on_post_save, sender=sender)
            models.signals.pre_delete.connect(ExtendedModel.on_pre_delete, sender=sender)
            models.signals.post_delete.connect(ExtendedModel.on_post_delete, sender=sender)

    def connect_m2m_signal(self, sender):
        from django.db import models
        from mcod.core.db.models import ExtendedModel
        models.signals.m2m_changed.connect(ExtendedModel.on_m2m_changed, sender=sender)


class CoreConfig(AppConfig):
    name = 'core'
