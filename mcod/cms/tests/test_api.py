import pytest
from pytest_bdd import scenario


@pytest.mark.depends_on_component
@pytest.mark.component_cms
@scenario(
    "features/cms_api_endpoints.feature",
    "Check every CMS API's endpoint response for valid status_code",
)
def test_check_every_cms_apis_endpoint_response_for_valid_status_code(settings):
    assert settings.ROOT_URLCONF == "mcod.urls_cms"
