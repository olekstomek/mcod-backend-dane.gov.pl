from pytest_bdd import scenarios

from mcod.unleash import is_enabled

if is_enabled('S22_sparql_object_management.be'):
    scenarios('features/organization_sparql.feature')
