import pytest
from pytest_bdd import scenarios

# All tests in this module depend on component
pytestmark = [pytest.mark.depends_on_component, pytest.mark.component_api]

scenarios(
    "features/account.feature",
    "features/change_password.feature",
    "features/login.feature",
    "features/logout.feature",
    "features/resend_activation_email.feature",
    "features/reset_password_confirm.feature",
    "features/dashboard.feature",
    "features/meetings_api.feature",
    "features/dashboard_schedules.feature",
)
