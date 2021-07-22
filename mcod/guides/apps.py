from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from mcod.core.apps import ExtendedAppMixin


class GuidesConfig(ExtendedAppMixin, AppConfig):
    name = 'mcod.guides'
    verbose_name = _('Portal guide')

    def ready(self):
        pass
        # from mcod.guides.models import Guide, GuideTrash, Step
        # self.connect_core_signals(Guide)
        # self.connect_core_signals(GuideTrash)
        # self.connect_core_signals(Step)
