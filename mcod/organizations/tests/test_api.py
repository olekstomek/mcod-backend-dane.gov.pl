import pytest
from falcon import HTTP_OK, testing

from mcod.api import app
from mcod.core.tests.helpers.elasticsearch import ElasticCleanHelper


@pytest.fixture
def client14():
    return testing.TestClient(app, headers={
        'X-API-VERSION': '1.4',
        'Accept-Language': 'pl'
    })


@pytest.mark.django_db
class TestInstitutions(ElasticCleanHelper):

    def test_response_institutions_list_slug_in_link(self, valid_organization, client14):
        resp = client14.simulate_get('/institutions/')
        assert HTTP_OK == resp.status
        assert f"{valid_organization.id},{valid_organization.slug}" in resp.json['data'][0]['links']['self']

    def test_response_institutions_details_slug_in_link(self, valid_organization, client14):
        resp = client14.simulate_get(f'/institutions/{valid_organization.id}')
        assert HTTP_OK == resp.status
        assert f"{valid_organization.id},{valid_organization.slug}" in resp.json['data']['links']['self']

    def test_routes_id_and_slug_in_link_institution_details(self, valid_organization, client14):
        resp = client14.simulate_get(f"/institutions/{valid_organization.id},{valid_organization.slug}")
        assert HTTP_OK == resp.status
        assert "institution" == resp.json['data']['type']

    def test_routes_id_without_slug_in_link_institution_details(self, valid_organization, client14):
        resp = client14.simulate_get(f"/institutions/{valid_organization.id}")
        assert HTTP_OK == resp.status
        assert "institution" == resp.json['data']['type']

    def test_routes_id_and_slug_in_link_institution_datasets_list(self, valid_organization, valid_dataset, client14):
        resp = client14.simulate_get(f"/institutions/{valid_organization.id},{valid_organization.slug}/datasets")
        assert HTTP_OK == resp.status
        assert "dataset" == resp.json['data'][0]['type']

    def test_routes_id_without_slug_in_link_institution_datasets_list(self, valid_organization, valid_dataset,
                                                                      client14):
        resp = client14.simulate_get(f"/institutions/{valid_organization.id}/datasets")
        assert HTTP_OK == resp.status
        assert "dataset" == resp.json['data'][0]['type']
