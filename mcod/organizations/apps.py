from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from mcod.core.apps import ExtendedAppMixin


class OrganizationsConfig(ExtendedAppMixin, AppConfig):
    name = 'mcod.organizations'
    verbose_name = _('Institutions')

    def ready(self):
        from mcod.organizations.models import Organization, OrganizationTrash
        self.connect_core_signals(Organization)
        self.connect_core_signals(OrganizationTrash)
