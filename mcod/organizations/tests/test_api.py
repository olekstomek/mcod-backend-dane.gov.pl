from typing import Dict

import pytest
from falcon import HTTP_OK, testing
from pytest_bdd import scenarios

from mcod.core.tests.helpers.tasks import run_on_commit_events
from mcod.organizations.factories import OrganizationFactory

# All tests in this module depend on component
pytestmark = [pytest.mark.depends_on_component, pytest.mark.component_api]

scenarios(
    "features/organization_datasets_list_api.feature",
    "features/organizations_list_api.feature",
    "features/organization_remove_api.feature",
)


@pytest.mark.elasticsearch
def test_response_institutions_list_slug_in_link(institution, client14):
    resp = client14.simulate_get("/institutions/")
    assert HTTP_OK == resp.status
    assert f"{institution.id},{institution.slug}" in resp.json["data"][0]["links"]["self"]


@pytest.mark.elasticsearch
def test_response_institutions_details_slug_in_link(institution, client14):
    resp = client14.simulate_get(f"/institutions/{institution.id}")
    assert HTTP_OK == resp.status
    assert f"{institution.id},{institution.slug}" in resp.json["data"]["links"]["self"]


@pytest.mark.elasticsearch
def test_routes_id_and_slug_in_link_institution_details(institution, client14):
    resp = client14.simulate_get(f"/institutions/{institution.id},{institution.slug}")
    assert HTTP_OK == resp.status
    assert "institution" == resp.json["data"]["type"]


@pytest.mark.elasticsearch
def test_routes_id_without_slug_in_link_institution_details(institution, client14):
    resp = client14.simulate_get(f"/institutions/{institution.id}")
    assert HTTP_OK == resp.status
    assert "institution" == resp.json["data"]["type"]


@pytest.mark.elasticsearch
def test_routes_id_and_slug_in_link_institution_datasets_list(institution_with_datasets, client14):
    inst = institution_with_datasets
    resp = client14.simulate_get(f"/institutions/{inst.id},{inst.slug}/datasets")
    assert HTTP_OK == resp.status
    assert "dataset" == resp.json["data"][0]["type"]


@pytest.mark.elasticsearch
def test_routes_id_without_slug_in_link_institution_datasets_list(institution_with_datasets, client14):
    inst = institution_with_datasets
    resp = client14.simulate_get(f"/institutions/{inst.id}/datasets")
    assert HTTP_OK == resp.status
    assert "dataset" == resp.json["data"][0]["type"]


@pytest.mark.elasticsearch
def test_response_electronic_delivery_address_in_institution_detail(institution, client14):
    inst_id = institution.id
    resp = client14.simulate_get(f"/institutions/{inst_id}")
    assert HTTP_OK == resp.status
    assert "electronic_delivery_address" in resp.json["data"]["attributes"]


@pytest.mark.elasticsearch
@pytest.mark.parametrize(
    "api_version",
    ("1.0", "1.4"),
)
def test_pagination(api_clients: Dict[str, testing.TestClient], api_version: str):

    # GIVEN
    OrganizationFactory.create_batch(size=10, institution_type="developer")
    run_on_commit_events()
    client = api_clients[api_version]
    pagination_links = {"first", "last", "next", "self", "prev"}

    # WHEN
    resp = client.simulate_get("/institutions?page=3&per_page=2&type[term]=developer")

    # THEN
    assert resp.status == HTTP_OK
    assert len(resp.json) == 4  # 4 pages
    assert len(resp.json["data"]) == 2  # 2 results in current page
    assert set(resp.json["links"].keys()) == pagination_links  # all required links for pagination

    for link in pagination_links:
        assert "&type[term]=developer" in resp.json["links"][link]  # filter passed to links
