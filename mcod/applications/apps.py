from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from mcod.core.apps import ExtendedAppMixin


class ApplicationsConfig(ExtendedAppMixin, AppConfig):
    name = 'mcod.applications'
    verbose_name = _('Applications')

    def ready(self):
        from mcod.applications.models import Application, ApplicationTrash
        self.connect_core_signals(Application)
        self.connect_core_signals(ApplicationTrash)
        self.connect_m2m_signal(Application.datasets.through)
