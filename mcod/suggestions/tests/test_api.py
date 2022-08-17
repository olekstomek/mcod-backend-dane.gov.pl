import pytest
from falcon import HTTP_NOT_FOUND, HTTP_OK
from pytest_bdd import scenarios

from mcod.core.tests.helpers.tasks import run_on_commit_events
from mcod.suggestions.tasks import deactivate_accepted_dataset_submissions, send_data_suggestion

scenarios(
    'features/api/accepteddatasetsubmission_list.feature',
    'features/api/submissions.feature',
)


@pytest.mark.elasticsearch
def test_only_published_accepted_submission_in_public_list_view(
        public_accepted_dataset_submission, accepted_dataset_submission, client14):
    run_on_commit_events()
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


@pytest.mark.elasticsearch
def test_send_data_suggestion_task(suggestion):
    result = send_data_suggestion.delay(suggestion.id)
    assert result.result['suggestion'] == 'test suggestion notes'


@pytest.mark.elasticsearch
def test_deactivate_accepted_dataset_submissions_task():
    result = deactivate_accepted_dataset_submissions.delay()
    assert result.result['deactivated'] == 0
