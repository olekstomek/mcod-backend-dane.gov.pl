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
class TestApplicationsAPIRoutes(ElasticCleanHelper):

    def test_applications_routes(self, valid_application, client14):
        paths = [
            "/applications",
            f'/applications/{valid_application.id}',
            f'/applications/{valid_application.id},{valid_application.slug}',
            f'/applications/{valid_application.id}/datasets',
            f'/applications/{valid_application.id},{valid_application.slug}/datasets',
        ]

        for p in paths:
            resp = client14.simulate_get(p)
            assert resp.status == HTTP_OK


@pytest.mark.django_db
class TestApplicationsAPISlugInResponses(ElasticCleanHelper):

    def test_response_applications_list_slug_in_link(self, valid_application, client14):
        resp = client14.simulate_get('/applications/')
        assert HTTP_OK == resp.status
        assert f"{valid_application.id}" in resp.json['data'][0]['links']['self']

    def test_response_application_details_slug_in_link(self, valid_application, client14):
        resp = client14.simulate_get(f'/applications/{valid_application.id}')
        assert HTTP_OK == resp.status
        assert f"{valid_application.id}" in resp.json['data']['links']['self']
