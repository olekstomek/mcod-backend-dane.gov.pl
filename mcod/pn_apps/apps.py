from importlib import import_module
from typing import List, Optional
from django.apps import AppConfig
from django.conf import settings
from bokeh.server.django.routing import Routing, RoutingConfiguration


class PnAppsConfig(AppConfig):
    name = label = 'mcod.pn_apps'
    verbose_name = "Panel Apps"

    _routes: Optional[RoutingConfiguration] = None

    @property
    def bokeh_apps(self) -> List[Routing]:
        module = settings.PN_APPS_URLCONF
        url_conf = import_module(module) if isinstance(module, str) else module
        return url_conf.bokeh_apps

    @property
    def routes(self) -> RoutingConfiguration:
        if self._routes is None:
            self._routes = RoutingConfiguration(self.bokeh_apps)
        return self._routes
