from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from mcod.core.apps import ExtendedAppMixin


class ResourcesConfig(ExtendedAppMixin, AppConfig):
    name = 'mcod.resources'
    verbose_name = _('Resources')

    def ready(self):
        from mcod.resources.models import Resource, ResourceTrash
        self.connect_core_signals(Resource)
        self.connect_core_signals(ResourceTrash)
