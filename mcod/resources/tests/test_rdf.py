from pytest_bdd import scenarios

from mcod.unleash import is_enabled

scenarios('features/resource_rdf.feature')
if is_enabled('S22_sparql_object_management.be'):
    scenarios('features/resource_sparql.feature')
