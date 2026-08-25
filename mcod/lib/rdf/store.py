from django.conf import settings
from rdflib.plugins.stores.sparqlstore import (
    SPARQLStore as BaseSPARQLStore,
    SPARQLUpdateStore as BaseSPARQLUpdateStore,
)

from mcod.core.api.rdf.namespaces import NAMESPACES
from mcod.core.api.rdf.profiles.dcat_ap import DCATCatalog
from mcod.lib.extended_graph import ExtendedGraph
from mcod.lib.rdf import extra_triples


class SPARQLStore(BaseSPARQLStore):
    pass


class SPARQLUpdateStore(BaseSPARQLUpdateStore):

    def add_object(self, obj):
        query, ns = obj.as_sparql_create_query()
        self.update(query, initNs=ns)

    def get_catalog_metadata_create_query(self, context):
        catalog = DCATCatalog()
        triples = catalog.to_triples(context)
        triples_str = "\n".join(f"{s.n3()} {p.n3()} {o.n3()} ." for s, p, o in triples)
        return f"""
            INSERT DATA {{
                {triples_str}
            }}
        """

    def add_catalog_metadata(self, context):
        self.update(self.get_catalog_metadata_create_query(context))

    def delete_catalog_metadata(self):
        self.update(self.get_catalog_metadata_delete_query())

    def get_catalog_metadata_delete_query(self):
        catalog = DCATCatalog()
        catalog_subject = catalog.get_subject({}).n3()
        return f"""
            DELETE {{
                ?s ?p ?o .
                ?o ?p1 ?o1 .
            }}
            WHERE {{
                ?s ?p ?o .
                FILTER (?s = {catalog_subject}) .
                OPTIONAL {{
                    ?o ?p1 ?o1 .
                    FILTER (isBlank(?o))
                }}
            }}
        """

    def get_object_graph(self, query):
        g = ExtendedGraph(ordered=True)
        for prefix, namespace in NAMESPACES.items():
            g.bind(prefix, namespace)
        response = self.query(query)
        for row in response:
            g.add(row)
        return g

    def get_catalog(self, **kwargs):
        limit = kwargs.get("per_page", 1000)
        rdf_url_pattern = f"^{settings.BASE_URL}/pl/dataset/[0-9]+,([a-z]|-)+$"
        query = f"""
            CONSTRUCT {{
                ?s ?p ?o .
                ?o ?p1 ?o1 .
            }}
            WHERE {{
                ?s ?p ?o .
                OPTIONAL {{ ?o ?p1 ?o1 }}
                FILTER(REGEX(str(?s), "{rdf_url_pattern}"))
            }}
            LIMIT {limit}
        """
        g = self.get_object_graph(query)
        if len(g):
            for triple in extra_triples.EXTRA_DATASET_TRIPLES:
                g.add(triple)
        return g

    def get_dataset_graph(self, **kwargs):
        dataset_id = kwargs["id"]
        dataset_slug = kwargs.get("slug")
        suffix = f",{dataset_slug}" if dataset_slug else ""
        url = f"{settings.BASE_URL}/pl/dataset/{dataset_id}{suffix}"
        query = f"""
            CONSTRUCT {{
                ?s ?p ?o .
                ?o ?p1 ?o1 .
            }}
            WHERE {{
                ?s ?p ?o .
                OPTIONAL {{ ?o ?p1 ?o1 }}
                FILTER (strstarts(str(?s), '{url}'))
            }}
        """
        g = self.get_object_graph(query)
        if len(g):
            for triple in extra_triples.EXTRA_DATASET_TRIPLES:
                g.add(triple)
        return g

    def get_resource_graph(self, **kwargs):
        dataset_id = kwargs["id"]
        resource_id = kwargs["res_id"]
        url = f"{settings.BASE_URL}/pl/dataset/{dataset_id}/resource/{resource_id}"
        query = f"""
            CONSTRUCT {{
                <{url}> ?p ?o .
                ?o ?p1 ?o1 .
            }}
            WHERE {{
                <{url}> ?p ?o .
                OPTIONAL {{ ?o ?p1 ?o1 }}
            }}
        """
        g = self.get_object_graph(query)
        if len(g):
            for triple in extra_triples.EXTRA_RESOURCE_TRIPLES:
                g.add(triple)
        return g


def get_sparql_store(readonly=False, return_format="xml", external_sparql_endpoint=None):
    if readonly:
        params = {
            "auth": (settings.SPARQL_USER, settings.SPARQL_PASSWORD),
            "query_endpoint": settings.SPARQL_QUERY_ENDPOINT,
            "method": "POST_FORM",
            "returnFormat": return_format,
        }
        if external_sparql_endpoint == "kronika":
            params["query_endpoint"] = settings.KRONIKA_SPARQL_URL
            params["returnFormat"] = "json"
        return SPARQLStore(**params)

    params = {
        "auth": (settings.SPARQL_USER, settings.SPARQL_PASSWORD),
        "query_endpoint": settings.SPARQL_QUERY_ENDPOINT,
        "update_endpoint": settings.SPARQL_UPDATE_ENDPOINT,
    }
    return SPARQLUpdateStore(**params)
