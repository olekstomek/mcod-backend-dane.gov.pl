import pytest
from falcon import HTTP_OK, HTTP_CREATED
from falcon import testing

from mcod.api import app
from mcod.core.tests.helpers.elasticsearch import ElasticCleanHelper
from mcod.datasets.models import Dataset
from mcod.resources.models import Resource


@pytest.fixture
def client14():
    return testing.TestClient(app, headers={
        'X-API-VERSION': '1.4',
        'Accept-Language': 'pl'
    })


@pytest.mark.django_db
def test_dates_in_list_views_api14(valid_dataset, valid_resource, client14):
    resp = client14.simulate_get('/datasets')
    assert HTTP_OK == resp.status
    assert valid_dataset.id
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data'][0]['attributes']


@pytest.mark.django_db
def test_dates_in_detail_views_api14(valid_dataset, client14):
    _rid = valid_dataset.id
    resp = client14.simulate_get('/datasets/{}/'.format(_rid))
    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data']['attributes']

    assert resp.json['data']['attributes']['modified'] == valid_dataset.modified.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert resp.json['data']['attributes']['created'] == valid_dataset.created.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert resp.json['data']['attributes']['verified'] == valid_dataset.created.strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.mark.django_db
def test_data_date_with_resource_views_api14(valid_dataset, valid_resource, client14):
    id_ = valid_dataset.id
    valid_resource.revalidate()

    resp = client14.simulate_get('/datasets/{}/'.format(id_))
    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data']['attributes']

    rs = Resource.objects.get(pk=valid_resource.id)
    assert resp.json['data']['attributes']['modified'] == valid_dataset.modified.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert resp.json['data']['attributes']['created'] == valid_dataset.created.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert resp.json['data']['attributes']['verified'] == rs.verified.strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.mark.django_db
def test_dates_in_list_views_api14_in_path(valid_dataset, valid_resource, client14):
    resp = client14.simulate_get('/1.4/datasets/')
    assert HTTP_OK == resp.status
    assert valid_dataset.id
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data'][0]['attributes']


@pytest.mark.django_db
def test_dates_in_detail_views_api14_in_path(valid_dataset, client14):
    _rid = valid_dataset.id
    resp = client14.simulate_get('/1.4/datasets/{}/'.format(_rid))
    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data']['attributes']

    assert resp.json['data']['attributes']['modified'] == valid_dataset.modified.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert resp.json['data']['attributes']['created'] == valid_dataset.created.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert resp.json['data']['attributes']['verified'] == valid_dataset.verified.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert resp.json.get("jsonapi")


@pytest.mark.django_db
def test_datasets_dates_in_list_views(valid_dataset, client):
    resp = client.simulate_get('/datasets/')
    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data'][0]['attributes']


@pytest.mark.django_db
def test_dataset_dates_in_detail_views(valid_dataset, valid_resource, client):
    _id = valid_dataset.id
    valid_resource.revalidate()
    resp = client.simulate_get('/datasets/{}/'.format(_id))

    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data']['attributes']

    ds = Dataset.objects.get(pk=valid_dataset.id)
    assert resp.json['data']['attributes']['modified'] == str(valid_dataset.modified)
    assert resp.json['data']['attributes']['created'] == str(valid_dataset.created)
    assert resp.json['data']['attributes']['verified'] == str(ds.verified)


@pytest.mark.django_db
def test_datasets_dates_in_list_views_api_1_0_in_path(valid_dataset, client):
    resp = client.simulate_get('/1.0/datasets/')
    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data'][0]['attributes']


@pytest.mark.django_db
def test_dataset_dates_in_detail_views_api_1_0_in_path(valid_dataset, valid_resource, client):
    _id = valid_dataset.id
    valid_resource.revalidate()
    resp = client.simulate_get('/1.0/datasets/{}/'.format(_id))

    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data']['attributes']

    ds = Dataset.objects.get(pk=valid_dataset.id)
    assert resp.json['data']['attributes']['modified'] == str(valid_dataset.modified)
    assert resp.json['data']['attributes']['created'] == str(valid_dataset.created)
    assert resp.json['data']['attributes']['verified'] == str(ds.verified)


@pytest.mark.django_db
def test_dataset_reportcomment(valid_dataset, client14):
    resp = client14.simulate_post(
        path=f'/datasets/{valid_dataset.id}/comments',
        json={
            'data':
                {
                    'type': 'comment',
                    'attributes':
                        {
                            'comment': "123"
                        }
                }
        }
    )

    assert resp.status == HTTP_CREATED


@pytest.mark.django_db
class TestInstitutionsRelation(ElasticCleanHelper):

    def test_slug_in_organization_link_datasets_list(self, valid_dataset, valid_organization, client14):
        resp = client14.simulate_get('/datasets/')
        assert HTTP_OK == resp.status
        assert resp.json['data'][0]['relationships']['institution']['links']['related'].endswith(
            f"{valid_organization.id},{valid_organization.slug}"
        )

    def test_slug_in_organization_link_dataset_details(self, valid_dataset, valid_organization, client14):
        resp = client14.simulate_get(f'/datasets/{valid_dataset.id}')
        assert HTTP_OK == resp.status
        assert resp.json['data']['relationships']['institution']['links']['related'].endswith(
            f"{valid_organization.id},{valid_organization.slug}"
        )


@pytest.mark.django_db
class TestDatasetsAPIRoutes(ElasticCleanHelper):

    def test_datasets_routes(self, valid_dataset, client14):
        paths = [
            "/datasets",
            f'/datasets/{valid_dataset.id}',
            f'/datasets/{valid_dataset.id},{valid_dataset.slug}',
            f'/datasets/{valid_dataset.id}/resources',
            f'/datasets/{valid_dataset.id},{valid_dataset.slug}/resources',
        ]

        for p in paths:
            resp = client14.simulate_get(p)
            assert resp.status == HTTP_OK


@pytest.mark.django_db
class TestDatasetsAPISlugInResponses(ElasticCleanHelper):

    def test_response_datasets_list_slug_in_link(self, valid_dataset, client14):
        resp = client14.simulate_get('/datasets/')
        assert HTTP_OK == resp.status
        assert f"{valid_dataset.id},{valid_dataset.slug}" in resp.json['data'][0]['links']['self']

    def test_response_dataset_details_slug_in_link(self, valid_dataset, client14):
        resp = client14.simulate_get(f'/datasets/{valid_dataset.id}')
        assert HTTP_OK == resp.status
        assert f"{valid_dataset.id},{valid_dataset.slug}" in resp.json['data']['links']['self']
