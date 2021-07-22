from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from rdflib.plugin import register
from rdflib.query import ResultParser
from rdflib.parser import Parser


class HarvesterConfig(AppConfig):
    name = 'mcod.harvester'
    verbose_name = _('Data Sources')

    def ready(self):
        import mcod.harvester.signals.handlers  # noqa
        register(
            'application/rdf+xml; charset=UTF-8', ResultParser,
            'rdflib.plugins.sparql.results.graph', 'GraphResultParser')
        register(
            'application/rdf+xml; charset=UTF-8', Parser,
            'rdflib.plugins.parsers.rdfxml', 'RDFXMLParser')
