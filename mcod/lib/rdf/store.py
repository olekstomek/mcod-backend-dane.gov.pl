from rdflib import BNode
from rdflib.plugins.stores.sparqlstore import (
    SPARQLStore as BaseSPARQLStore,
    SPARQLUpdateStore as BaseSPARQLUpdateStore,
)

from mcod import settings
from mcod.core.api.rdf.namespaces import NAMESPACES
from mcod.lib.extended_graph import ExtendedGraph
from mcod.lib.rdf import extra_triples


class SPARQLStore(BaseSPARQLStore):
    pass


class SPARQLUpdateStore(BaseSPARQLUpdateStore):

    def add_object(self, obj):
        query, ns = obj.as_sparql_create_query()
        self.update(query, initNs=ns)

    def get_object_graph(self, query):
        g = ExtendedGraph(ordered=True)
        for prefix, namespace in NAMESPACES.items():
            g.bind(prefix, namespace)
        response = self.query(query)
        for row in response:
            g.add(row)
        return g

    def get_catalog(self, **kwargs):
        limit = kwargs.get('per_page', 1000)
        query = '''CONSTRUCT {?s ?p ?o . ?o ?p1 ?o1} WHERE
        { ?s ?p ?o . OPTIONAL{ ?o ?p1 ?o1}
        FILTER(REGEX(str(?s), "%(rdf_url_pattern)s"))
        }
        LIMIT %(limit)s''' % {
            'rdf_url_pattern': f'^{settings.BASE_URL}/pl/dataset/[0-9]+,([a-z]|-)+$',
            'limit': limit,
        }
        g = self.get_object_graph(query)
        if len(g):
            for triple in extra_triples.EXTRA_DATASET_TRIPLES:
                g.add(triple)
        return g

    def get_dataset_graph(self, **kwargs):
        dataset_id = kwargs['id']
        dataset_slug = kwargs.get('slug')
        suffix = f',{dataset_slug}' if dataset_slug else ''
        url = f'{settings.BASE_URL}/pl/dataset/{dataset_id}{suffix}'
        query = '''
        CONSTRUCT {?s ?p ?o . ?o ?p1 ?o1} WHERE
        { ?s ?p ?o . OPTIONAL{ ?o ?p1 ?o1}
        FILTER (strstarts(str(?s), '%(rdf_url)s'))
        }
        ''' % {'rdf_url': url}
        g = self.get_object_graph(query)
        if len(g):
            for triple in extra_triples.EXTRA_DATASET_TRIPLES:
                g.add(triple)
        return g

    def get_resource_graph(self, **kwargs):
        dataset_id = kwargs['id']
        resource_id = kwargs['res_id']
        url = f'{settings.BASE_URL}/pl/dataset/{dataset_id}/resource/{resource_id}'
        query = '''
        CONSTRUCT {<%(rdf_url)s> ?p ?o . ?o ?p1 ?o1} WHERE {
        <%(rdf_url)s> ?p ?o . OPTIONAL{ ?o ?p1 ?o1}}
        ''' % {'rdf_url': url}
        g = self.get_object_graph(query)
        if len(g):
            for triple in extra_triples.EXTRA_RESOURCE_TRIPLES:
                g.add(triple)
        return g


def my_bnode_ext(node):
    # https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.plugins.stores.html#rdflib.plugins.stores.sparqlstore.SPARQLStore  # noqa
    if isinstance(node, BNode):
        return '<bnode:b%s>' % node


def get_sparql_store(readonly=False, return_format='xml'):
    if readonly:
        params = {
            'auth': (settings.SPARQL_USER, settings.SPARQL_PASSWORD),
            'endpoint': settings.SPARQL_QUERY_ENDPOINT,
            'method': 'POST',
            'returnFormat': return_format,
        }
        return SPARQLStore(**params)

    params = {
        'auth': (settings.SPARQL_USER, settings.SPARQL_PASSWORD),
        'queryEndpoint': settings.SPARQL_QUERY_ENDPOINT,
        'update_endpoint': settings.SPARQL_UPDATE_ENDPOINT,
        'node_to_sparql': my_bnode_ext,
    }
    return SPARQLUpdateStore(**params)
