from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from mcod.core.apps import ExtendedAppMixin


class ResourcesConfig(ExtendedAppMixin, AppConfig):
    name = 'mcod.resources'
    verbose_name = _('Resources')

    def ready(self):
        from mcod.resources.models import Resource, ResourceTrash, Chart, ResourceFile, Supplement
        from mcod.core.registries import rdf_serializers_registry as rsr
        from mcod.resources.serializers import ResourceRDFResponseSchema
        self.connect_core_signals(Resource)
        self.connect_core_signals(ResourceFile)
        self.connect_core_signals(ResourceTrash)
        self.connect_core_signals(Chart)
        self.connect_m2m_signal(Resource.special_signs.through)
        self.connect_m2m_signal(Resource.regions.through)
        rsr.register(ResourceRDFResponseSchema)
        self.connect_history(Resource, Chart, Supplement)
