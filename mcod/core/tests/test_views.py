import pytest
from pytest_bdd import scenarios

pytestmark = [pytest.mark.depends_on_component, pytest.mark.component_api]

scenarios("features/api_spec.feature")
