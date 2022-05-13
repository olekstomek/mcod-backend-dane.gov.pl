from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from mcod.core.apps import ExtendedAppMixin


class ApplicationsConfig(ExtendedAppMixin, AppConfig):
    name = 'mcod.applications'
    verbose_name = _('Applications')

    def ready(self):
        from mcod.applications.models import Application, ApplicationProposal, ApplicationTrash
        from mcod.unleash import is_enabled
        if not is_enabled('S49_delete_application_app.be'):
            self.connect_core_signals(Application)
            self.connect_core_signals(ApplicationTrash)
            self.connect_m2m_signal(Application.datasets.through)
            self.connect_history(Application, ApplicationProposal)
