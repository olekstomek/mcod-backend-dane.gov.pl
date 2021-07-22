from django.apps import AppConfig


class CmsConfig(AppConfig):
    name = 'mcod.cms'
    label = 'cms'

    def ready(self):
        from django.db import models
        from mcod.cms.models.base import BasePage
        from mcod.cms import models as cms_models
        for model_name in cms_models.__all__:
            page_model = getattr(cms_models, model_name)
            models.signals.post_save.connect(BasePage.on_post_save, sender=page_model)
            models.signals.pre_delete.connect(BasePage.on_pre_delete, sender=page_model)
