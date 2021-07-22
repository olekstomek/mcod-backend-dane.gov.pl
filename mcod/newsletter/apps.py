from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NewsletterConfig(AppConfig):
    name = 'mcod.newsletter'
    verbose_name = _('Newsletter')

    def ready(self):
        pass
