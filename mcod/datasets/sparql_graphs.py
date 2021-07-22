import marshmallow as ma
from rdflib import ConjunctiveGraph
from rdflib import URIRef
from mcod.core.api.rdf.sparql_graphs import SparqlGraph
import mcod.core.api.rdf.namespaces as ns
from mcod.datasets.serializers import DatasetRDFResponseSchema
from mcod.datasets.models import Dataset
from mcod.resources.models import Resource
from mcod.organizations.models import Organization
from mcod.categories.models import Category


class DatasetSparqlGraph(SparqlGraph, DatasetRDFResponseSchema):
    model = Dataset
    related_models = [Resource, Category, Organization]
    parent_model = Organization
    parent_fk = 'organization'
    include_nested_triples = False
    related_condition_attr = 'license_chosen'

    @ma.pre_dump(pass_many=True)
    def prepare_data(self, data, many, **kwargs):
        return data

    @ma.pre_dump(pass_many=True)
    def extract_pagination(self, data, many, **kwargs):
        return data

    @ma.post_dump(pass_many=True)
    def prepare_graph(self, data, many, **kwargs):
        graph = ConjunctiveGraph()
        self.add_bindings(graph=graph)
        if many:
            triples = []
            for _triples in data:
                triples.extend(_triples)
        else:
            triples = data

        for triple in triples:
            graph.add(triple)
        return graph

    def get_related_from_instance(self, instance):
        if isinstance(instance, Resource):
            return instance.dataset
        if isinstance(instance, Category):
            return instance.datasets.filter(status='published')
        if isinstance(instance, Organization):
            return instance.datasets.filter(status='published')

    def _prepare_catalog_entry(self, instance):
        catalog = self.get_rdf_class_for_catalog()()
        catalog_subject = catalog.get_subject({})
        catalog_node = f'{catalog_subject.n3()} {URIRef(ns.DCAT.Dataset).n3()}' \
                       f' {URIRef(instance.frontend_absolute_url).n3()} . '
        return catalog_subject.n3(), catalog_node

    def create(self, instance):
        _ns, instance_nodes = self._prepare_query_data(instance)
        catalog_subject, catalog_node = self._prepare_catalog_entry(instance)
        instance_nodes[catalog_subject] = catalog_node
        return self._get_create_query(instance_nodes), _ns

    def delete(self, instance):
        ns, instance_nodes = self._prepare_query_data(instance)
        catalog_subject, catalog_node = self._prepare_catalog_entry(instance)
        instance_nodes[catalog_subject] = catalog_node
        return self._get_delete_query(instance_nodes), ns
