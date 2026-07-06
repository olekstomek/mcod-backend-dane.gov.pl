from typing import Dict, Optional

import pytest
from falcon.testing.client import TestClient as FalconTestClient

from mcod.datasets.factories import DatasetFactory
from mcod.suggestions.models import DatasetComment


@pytest.fixture
def default_dataset_comment_data():
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
def test_dataset_comment_created(
    api_version: str,
    optional_field: Optional[str],
    api_clients: Dict[str, FalconTestClient],
    default_dataset_comment_data: Dict[str, Optional[str]],
):
    # GIVEN
    assert DatasetComment.objects.count() == 0
    dataset = DatasetFactory.create()
    api_client: FalconTestClient = api_clients[api_version]
    if optional_field is not None:
        default_dataset_comment_data.pop(optional_field)
    data = {"data": {"type": "submission", "attributes": default_dataset_comment_data}}

    # WHEN
    response = api_client.simulate_post(
        path=f"/datasets/{dataset.pk}/comments",
        json=data,
    )

    # THEN
    assert response.status_code == 201
    assert DatasetComment.objects.count() == 1
    dataset_comment = DatasetComment.objects.last()
    assert dataset_comment.comment == default_dataset_comment_data["comment"]
    assert dataset_comment.dataset_id == dataset.pk


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
def test_dataset_comment_create_validation_errors(
    api_version: str,
    invalid_update: Dict[str, str],
    api_clients: Dict[str, FalconTestClient],
    default_dataset_comment_data: Dict[str, str],
):
    api_client: FalconTestClient = api_clients[api_version]
    default_dataset_comment_data.update(invalid_update)
    payload = {"data": {"type": "submission", "attributes": default_dataset_comment_data}}
    dataset = DatasetFactory.create()

    response = api_client.simulate_post(
        path=f"/datasets/{dataset.pk}/comments",
        json=payload,
    )

    assert response.status_code == 422
