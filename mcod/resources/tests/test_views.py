from typing import Dict, Optional

import pytest
from django.conf import settings
from falcon import HTTP_OK
from falcon.testing.client import TestClient as FalconTestClient

from mcod.core.tests.helpers.tasks import run_on_commit_events
from mcod.resources.factories import ResourceFactory
from mcod.suggestions.models import ResourceComment


@pytest.mark.elasticsearch
def test_links_to_indexed_data(client14, tabular_resource):
    run_on_commit_events()
    response = client14.simulate_get(f"/resources/{tabular_resource.id}")
    assert HTTP_OK == response.status
    body = response.json
    assert "relationships" in body["data"]
    assert "tabular_data" in body["data"]["relationships"]
    assert "links" in body["data"]["relationships"]["tabular_data"]
    assert "related" in body["data"]["relationships"]["tabular_data"]["links"]
    link = body["data"]["relationships"]["tabular_data"]["links"]["related"]
    assert link == f"{settings.API_URL}/1.4/resources/{tabular_resource.id}/data"

    response = client14.simulate_get(f"/resources/?id={tabular_resource.id}")
    assert HTTP_OK == response.status
    body = response.json
    data = body["data"][0]
    assert "relationships" in data
    assert "tabular_data" in data["relationships"]
    assert "links" in data["relationships"]["tabular_data"]
    assert "related" in data["relationships"]["tabular_data"]["links"]
    link = data["relationships"]["tabular_data"]["links"]["related"]
    assert link == f"{settings.API_URL}/1.4/resources/{tabular_resource.id}/data"


@pytest.mark.elasticsearch
def test_links_to_no_data_resource(client14, no_data_resource):
    response = client14.simulate_get(f"/resources/{no_data_resource.id}")
    assert HTTP_OK == response.status
    body = response.json
    assert "relationships" in body["data"]
    assert "tabular_data" not in body["data"]["relationships"]
    assert "geo_data" not in body["data"]["relationships"]


@pytest.fixture
def default_resource_comment_data():
    return {
        "applicant_full_name": "John Doe",
        "applicant_email": "john@doe.com",
        "comment": "Some comment",
    }


@pytest.mark.parametrize("api_version", ["1.0", "1.4"])
@pytest.mark.parametrize(
    "optional_field",
    (
        None,
        "applicant_full_name",
        "applicant_email",
    ),
)
def test_resource_comment_created(
    api_version: str,
    optional_field: Optional[str],
    api_clients: Dict[str, FalconTestClient],
    default_resource_comment_data: Dict[str, Optional[str]],
):
    # GIVEN
    assert ResourceComment.objects.count() == 0
    resource = ResourceFactory.create()
    api_client: FalconTestClient = api_clients[api_version]
    if optional_field is not None:
        default_resource_comment_data.pop(optional_field)
    data = {"data": {"type": "submission", "attributes": default_resource_comment_data}}

    # WHEN
    response = api_client.simulate_post(
        path=f"/resources/{resource.pk}/comments",
        json=data,
    )

    # THEN
    assert response.status_code == 201
    assert ResourceComment.objects.count() == 1
    res_comment = ResourceComment.objects.last()
    assert res_comment.comment == default_resource_comment_data["comment"]
    assert res_comment.resource_id == resource.pk


@pytest.mark.parametrize("api_version", ["1.0", "1.4"])
@pytest.mark.parametrize(
    "invalid_update",
    [
        {"applicant_email": "not-an-email"},
        {"applicant_email": "a" * 255},
        {"applicant_email": ""},
        {"applicant_full_name": "a" * 301},
        {"applicant_full_name": ""},
        {"comment": "a" * 3001},
        {"comment": ""},
        {"comment": None},
    ],
)
def test_resource_comment_validation_errors(
    api_version: str,
    invalid_update: Dict[str, str],
    api_clients: Dict[str, FalconTestClient],
    default_resource_comment_data: Dict[str, str],
):
    api_client: FalconTestClient = api_clients[api_version]
    default_resource_comment_data.update(invalid_update)
    payload = {"data": {"type": "submission", "attributes": default_resource_comment_data}}
    resource = ResourceFactory.create()

    response = api_client.simulate_post(
        path=f"/resources/{resource.pk}/comments",
        json=payload,
    )

    assert response.status_code == 422
