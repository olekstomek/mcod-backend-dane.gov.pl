import pytest
from pytest_bdd import scenarios

# All tests in this module depend on component
pytestmark = [pytest.mark.depends_on_component, pytest.mark.component_api]

scenarios(
    "features/search.feature",
    "features/sparql.feature",
    "features/suggest.feature",
    "features/other_sparql_endpoints.feature",
)
