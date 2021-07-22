from mcod.core.api.rdf.sparql_graphs import SparqlGraph
from mcod.datasets.serializers import CategoryRDFNestedSchema
from mcod.categories.models import Category


class CategorySparqlGraph(CategoryRDFNestedSchema, SparqlGraph):
    model = Category
