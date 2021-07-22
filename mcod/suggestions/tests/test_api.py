from falcon import HTTP_OK, HTTP_NOT_FOUND
from pytest_bdd import scenarios
import pytest


scenarios('features/accepteddatasetsubmission_list_api.feature')


@pytest.mark.elasticsearch
def test_only_published_accepted_submission_in_public_list_view(
        public_accepted_dataset_submission, accepted_dataset_submission, client14):
    resp = client14.simulate_get('/submissions/accepted/public')
    assert HTTP_OK == resp.status
    assert len(resp.json['data']) == 1
    assert resp.json['data'][0]['attributes']['title'] == 'public test title'
    assert resp.json.get("jsonapi")


@pytest.mark.elasticsearch
def test_published_accepted_submission_in_public_details_view(
        public_accepted_dataset_submission, client14):
    obj_id = public_accepted_dataset_submission.pk
    resp = client14.simulate_get(f'/submissions/accepted/public/{obj_id}')
    assert HTTP_OK == resp.status
    assert resp.json['data']['attributes']['title'] == 'public test title'
    assert resp.json.get("jsonapi")


@pytest.mark.elasticsearch
def test_unpublished_accepted_submission_not_in_public_details_view(
        accepted_dataset_submission, client14):
    obj_id = accepted_dataset_submission.pk
    resp = client14.simulate_get(f'/submissions/accepted/public/{obj_id}')
    assert HTTP_NOT_FOUND == resp.status
