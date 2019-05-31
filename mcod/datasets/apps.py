from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from mcod.core.apps import ExtendedAppMixin


class DatasetsConfig(ExtendedAppMixin, AppConfig):
    name = 'mcod.datasets'
    verbose_name = _('Datasets')

    def ready(self):
        from mcod.datasets.models import Dataset, DatasetTrash
        self.connect_core_signals(Dataset)
        self.connect_core_signals(DatasetTrash)
        self.connect_m2m_signal(Dataset.tags.through)
