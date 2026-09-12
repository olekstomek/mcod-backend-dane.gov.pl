import pytest
from pytest_bdd import scenarios

# All tests in this module depend on component
pytestmark = [pytest.mark.depends_on_component, pytest.mark.component_api]

scenarios(
    "features/extra.feature",
    "features/schedule_agents_api.feature",
    "features/schedule_details_api.feature",
    "features/user_schedule_details_api.feature",
    "features/user_schedule_item_details_api.feature",
    "features/user_schedule_item_update_api.feature",
    "features/schedules_list_api.feature",
    "features/user_schedule_items_list_api.feature",
)
