import pytest
from pytest_bdd import scenarios

# All tests in this module depend on component
pytestmark = [pytest.mark.depends_on_component, pytest.mark.component_api]

scenarios(
    "features/notifications_api.feature",
    "features/query_watcher.feature",
    "features/subscriptions_api.feature",
)
