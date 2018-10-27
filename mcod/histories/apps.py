from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HistoriesConfig(AppConfig):
    name = 'mcod.histories'
    verbose_name = _('Histories')
