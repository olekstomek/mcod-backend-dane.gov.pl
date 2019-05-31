import pytest
from falcon import HTTP_OK, HTTP_NOT_FOUND, HTTP_UNPROCESSABLE_ENTITY
from openapi_core import create_spec
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.validation.response.validators import ResponseValidator
from pytest_bdd import scenario, when, then

from mcod.api import app
from mcod.core.tests.helpers.elasticsearch import ElasticCleanHelper
from mcod.core.tests.helpers.openapi_wrappers import FalconOpenAPIWrapper
from mcod.core.utils import jsonapi_validator
from mcod.resources.models import Resource


@pytest.fixture
def container():
    return {
        'request_data': {
            'method': 'GET',
            'path': '',
            'headers': {
                'X-API-VERSION': '1.4',
                'Accept-Language': 'pl'
            },
            'query': {
                'page': 1,
                'per_page': 20
            }
        }
    }


@pytest.mark.django_db
@scenario('features/tabular_view_test.feature', 'Test listing')
def test_tabular_view(client14):
    pass


@when('I search in tabular data rows')
def setup_query(tabular_resource, container):
    _rid = tabular_resource.id
    container['request_data']['method'] = 'GET'
    container['request_data']['path'] = '/resources/{}/data'.format(_rid)


@when('I send request')
def sent_request(client14, container):
    path = container['request_data']['path']
    resp = client14.simulate_get('{}/spec/1.4'.format(path))
    assert HTTP_OK == resp.status
    spec = create_spec(resp.json)
    req = FalconOpenAPIWrapper(
        app, **container['request_data']
    )

    validator = RequestValidator(spec)
    result = validator.validate(req)
    assert not result.errors

    validator = ResponseValidator(spec)
    result = validator.validate(req, req)
    assert not result.errors
    container['response'] = req.request


@then('check if response is ok')
def validate_response(resource, valid_response):
    _rid = resource.id
    resp = valid_response
    data = resp.json['data'][1]
    assert data['type'] == 'row'
    assert data['id'] == 'd4ff4c97-5d9e-56a5-9d7c-46547879b7ae'
    assert data['meta']['row_no'] == 2
    assert data['attributes']['col3'] == '2,290,000.00'
    assert data['relationships']['resource']['data']['id'] == str(_rid)

    assert resp.json['meta']['count'] == 1000
    assert len(resp.json['meta']) == 8
    assert len(resp.json['meta']['headers_map']) == 6
    assert 'title' in resp.json['meta']['headers_map']
    assert 'published_date' in resp.json['meta']['headers_map']
    assert resp.json['meta']['headers_map']['published_date'] == 'col4'
    assert len(resp.json['meta']['data_schema']['fields']) == 6
    links = resp.json['links']
    assert len(links) == 4
    assert links['self'] == 'http://falconframework.org/resources/{}/data?page=1'.format(_rid)
    assert links['first'] == 'http://falconframework.org/resources/{}/data?page=1'.format(_rid)
    assert links['last'] == 'http://falconframework.org/resources/{}/data?page=50'.format(_rid)
    assert links['next'] == 'http://falconframework.org/resources/{}/data?page=2'.format(_rid)


@pytest.mark.django_db
def test_tabular_data_api14(buzzfeed_fakenews_resource, client14):
    _rid = buzzfeed_fakenews_resource.id

    resp = client14.simulate_get('/resources/{}/data/spec/1.4'.format(_rid))
    assert HTTP_OK == resp.status
    spec = create_spec(resp.json)

    # Test tablular data format
    req = FalconOpenAPIWrapper(
        app, method='GET', path='/resources/{}/data'.format(_rid),
        headers={
            'X-API-VERSION': '1.4',
            'Accept-Language': 'pl'
        },

    )

    validator = RequestValidator(spec)
    result = validator.validate(req)
    assert not result.errors

    validator = ResponseValidator(spec)
    result = validator.validate(req, req)
    assert not result.errors

    resp = req.request

    assert HTTP_OK == resp.status
    valid, validated_data, errors = jsonapi_validator(resp.json)

    assert valid is True
    assert len(validated_data) == 20
    assert validated_data[0]['type'] == 'row'
    assert validated_data[0]['resource']['id'] == str(_rid)
    data = resp.json['data'][1]
    assert data['type'] == 'row'
    assert data['id'] == 'd4ff4c97-5d9e-56a5-9d7c-46547879b7ae'
    assert data['meta']['row_no'] == 2
    assert data['attributes']['col3'] == '2,290,000.00'
    assert data['relationships']['resource']['data']['id'] == str(_rid)

    assert resp.json['meta']['count'] == 1000
    assert len(resp.json['meta']) == 9
    assert len(resp.json['meta']['headers_map']) == 6
    assert 'title' in resp.json['meta']['headers_map']
    assert 'published_date' in resp.json['meta']['headers_map']
    assert resp.json['meta']['headers_map']['published_date'] == 'col4'
    assert len(resp.json['meta']['data_schema']['fields']) == 6
    links = resp.json['links']
    assert len(links) == 3
    assert links['self'] == 'http://falconframework.org/resources/{}/data?page=1'.format(_rid)
    assert links['last'] == 'http://falconframework.org/resources/{}/data?page=50'.format(_rid)
    assert links['next'] == 'http://falconframework.org/resources/{}/data?page=2'.format(_rid)

    # Test search
    req = FalconOpenAPIWrapper(
        app, method='GET', path='/resources/{}/data'.format(_rid),
        query={
            'q': 'col5:Crime',
            'per_page': 25
        },
        headers={
            'X-API-VERSION': '1.4',
            'Accept-Language': 'pl'
        }
    )

    validator = RequestValidator(spec)
    result = validator.validate(req)
    assert not result.errors

    validator = ResponseValidator(spec)
    result = validator.validate(req, req)
    assert not result.errors

    resp = req.request

    assert HTTP_OK == resp.status
    valid, validated_data, errors = jsonapi_validator(resp.json)
    assert valid is True
    assert len(validated_data) == 21
    meta = resp.json['meta']
    assert meta['count'] == 21
    links = resp.json['links']
    assert len(links) == 1
    assert links['self'] == 'http://falconframework.org/resources/{}/data?per_page=25&q=col5%3ACrime&page=1'.format(
        _rid)

    req = FalconOpenAPIWrapper(
        app, method='GET', path='/resources/{}/data'.format(_rid),
        query={
            'q': 'col1:President AND col5:Norwegian',
            'per_page': 5
        },
        headers={
            'X-API-VERSION': '1.4',
            'Accept-Language': 'pl'
        }
    )

    validator = RequestValidator(spec)
    result = validator.validate(req)
    assert not result.errors

    validator = ResponseValidator(spec)
    result = validator.validate(req, req)
    assert not result.errors

    resp = req.request

    assert HTTP_OK == resp.status
    valid, validated_data, errors = jsonapi_validator(resp.json)
    assert valid is True
    assert len(validated_data) == 1
    assert validated_data[0]['col3'] == '4347'
    assert validated_data[0]['col5'] == 'Norwegian Lawmakers'
    links = resp.json['links']
    assert len(links) == 1
    assert 'self' in links

    resp = client14.simulate_get('/resources/{}/data'.format(_rid),
                                 query_string='q=col4:[2018-12-01 TO *]&per_page=10&page=3')
    assert HTTP_OK == resp.status
    valid, validated_data, errors = jsonapi_validator(resp.json)
    assert valid is True
    assert len(validated_data) == 10
    meta = resp.json['meta']
    assert meta['count'] == 61
    links = resp.json['links']
    assert len(links) == 5
    assert links[
               'first'] == 'http://falconframework.org/resources/{}/' \
                           'data?page=1&per_page=10&q=col4%3A%5B2018' \
                           '-12-01%20TO%20%2A%5D'.format(_rid)
    assert links[
               'next'] == 'http://falconframework.org/resources/{}/' \
                          'data?page=4&per_page=10&q=col4%3A%5B2018' \
                          '-12-01%20TO%20%2A%5D'.format(_rid)
    assert links[
               'prev'] == 'http://falconframework.org/resources/{}/' \
                          'data?page=2&per_page=10&q=col4%3A%5B2018' \
                          '-12-01%20TO%20%2A%5D'.format(_rid)
    assert links[
               'last'] == 'http://falconframework.org/resources/{}/' \
                          'data?page=7&per_page=10&q=col4%3A%5B2018' \
                          '-12-01%20TO%20%2A%5D'.format(_rid)
    assert links[
               'self'] == 'http://falconframework.org/resources/{}/' \
                          'data?page=3&per_page=10&q=col4%3A%5B2018' \
                          '-12-01%20TO%20%2A%5D'.format(_rid)

    # Test single row
    req = FalconOpenAPIWrapper(
        app,
        method='GET',
        path='/resources/{}/data/6b73a62e-7af2-531c-87ae-df51a74af23f'.format(_rid),
        path_params={
            'id': '6b73a62e-7af2-531c-87ae-df51a74af23f'
        },
        path_pattern='/resources/%s/data/{id}' % _rid,
        headers={
            'X-API-VERSION': '1.4',
            'Accept-Language': 'pl'
        }
    )

    validator = RequestValidator(spec)
    result = validator.validate(req)
    assert not result.errors

    validator = ResponseValidator(spec)
    result = validator.validate(req, req)
    assert not result.errors

    resp = req.request

    assert HTTP_OK == resp.status
    valid, validated_data, errors = jsonapi_validator(resp.json)
    assert valid is True
    assert len(validated_data) == 9
    assert validated_data['col5'] == 'Norwegian Lawmakers'
    assert validated_data[
               'col1'] == 'President Trump Nominated for Nobel Peace Prize by ' \
                          'Norwegian Lawmakers'
    assert validated_data['resource']['id'] == str(_rid)
    data = resp.json['data']
    assert data['type'] == 'row'
    assert data['meta']['row_no'] == 774
    assert data['relationships']['resource']['data']['id'] == str(_rid)
    meta = resp.json['meta']
    assert len(meta) == 7
    assert len(meta['headers_map']) == 6
    assert 'title' in meta['headers_map']
    assert 'published_date' in meta['headers_map']
    assert meta['headers_map']['published_date'] == 'col4'
    assert len(meta['data_schema']['fields']) == 6

    links = resp.json['links']
    assert len(links) == 1
    assert links[
               'self'] == 'http://falconframework.org/resources/{}/' \
                          'data/6b73a62e-7af2-531c-87ae-df51a74af23f'.format(_rid)


@pytest.mark.django_db
def test_dates_in_list_views_api14(buzzfeed_fakenews_resource, client14):
    resp = client14.simulate_get('/resources/')
    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data'][0]['attributes']


@pytest.mark.django_db
def test_dates_in_list_views_api14_in_path(buzzfeed_fakenews_resource, client14):
    resp = client14.simulate_get('/1.4/resources/')
    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data'][0]['attributes']


@pytest.mark.django_db
def test_dates_in_detail_views_api14(buzzfeed_fakenews_resource, client14):
    _rid = buzzfeed_fakenews_resource.id
    resp = client14.simulate_get('/resources/{}/'.format(_rid))
    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified', 'data_date']:
        assert d_name in resp.json['data']['attributes']

    rs = Resource.objects.get(pk=buzzfeed_fakenews_resource.id)

    assert resp.json['data']['attributes']['modified'] == rs.modified.strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    assert resp.json['data']['attributes']['created'] == rs.created.strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    assert resp.json['data']['attributes']['verified'] == rs.verified.strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    assert resp.json['data']['attributes']['data_date'] == rs.data_date.strftime(
        "%Y-%m-%d")


@pytest.mark.django_db
def test_dates_in_list_views(buzzfeed_fakenews_resource, client):
    resp = client.simulate_get('/resources/')
    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified', 'data_date']:
        assert d_name in resp.json['data'][0]['attributes']


@pytest.mark.django_db
def test_dates_in_list_views_api_1_0_in_path(buzzfeed_fakenews_resource, client):
    resp = client.simulate_get('/1.0/resources/')
    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified', 'data_date']:
        assert d_name in resp.json['data'][0]['attributes']


@pytest.mark.django_db
def test_dates_in_detail_views(buzzfeed_fakenews_resource, client):
    _rid = buzzfeed_fakenews_resource.id

    assert buzzfeed_fakenews_resource.data_date is not None
    resp = client.simulate_get('/resources/{}/'.format(_rid))

    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data']['attributes']

    rs = Resource.objects.get(pk=buzzfeed_fakenews_resource.id)

    assert resp.json['data']['attributes']['modified'] == str(rs.modified)
    assert resp.json['data']['attributes']['created'] == str(rs.created)
    assert resp.json['data']['attributes']['verified'] == str(rs.verified)
    assert resp.json['data']['attributes']['data_date'] == str(rs.data_date)


@pytest.mark.django_db
class TestResourcesAPIRoutes(ElasticCleanHelper):

    def test_resource_routes(self, valid_resource, client14):
        paths = [
            "/resources",
            f'/resources/{valid_resource.id}',
            f'/resources/{valid_resource.id},{valid_resource.slug}',
        ]

        for p in paths:
            resp = client14.simulate_get(p)
            assert resp.status == HTTP_OK


@pytest.mark.django_db
class TestResourcesAPISlugInResponses(ElasticCleanHelper):

    def test_resources_list_slug_in_link(self, valid_resource, client14):
        resp = client14.simulate_get('/resources/')
        assert HTTP_OK == resp.status
        assert f"{valid_resource.id},{valid_resource.slug}" in resp.json['data'][0]['links']['self']

    def test_response_resources_details_slug_in_link(self, valid_resource, client14):
        resp = client14.simulate_get(f'/resources/{valid_resource.id}')
        assert HTTP_OK == resp.status
        assert f"{valid_resource.id},{valid_resource.slug}" in resp.json['data']['links']['self']


@pytest.mark.django_db
class TestComments:
    def test_valid_resource_comment(self, valid_resource, client14):
        resp = client14.simulate_post(
            path=f'/resources/{valid_resource.id}/comments',
            json={
                'data': {
                    'type': 'comment',
                    'attributes': {
                        'comment': "some valid\ncomment"
                    }
                }
            }
        )
        assert resp.status == HTTP_OK

        resp = client14.simulate_post(
            path=f'/resources/{valid_resource.id}/comments',
            json={
                'data': {
                    'type': 'comment',
                    'attributes': {
                        'comment': "123"
                    }
                }
            })
        assert resp.status == HTTP_OK

        resp = client14.simulate_post(
            path=f'/resources/{valid_resource.id}/comments',
            json={
                'data': {
                    'type': 'comment',
                    'attributes': {
                        'comment': "a" * 10 * 5
                    }
                }
            }
        )
        assert resp.status == HTTP_OK

    def test_comment_too_short(self, valid_resource, client14):
        resp = client14.simulate_post(
            path=f'/resources/{valid_resource.id}/comments',
            json={
                'data': {
                    'type': 'comment',
                    'attributes': {
                        'comment': "12"
                    }
                }
            }

        )

        assert resp.status == HTTP_UNPROCESSABLE_ENTITY
        assert resp.json['code'] == "entity_error"
        assert resp.json['description'] == "Błąd wartości pola"
        assert len(resp.json['errors']['data']['attributes']['comment'][0]) > 10

    def test_no_comment(self, valid_resource, client14):
        resp = client14.simulate_post(
            path=f'/resources/{valid_resource.id}/comments',
            json={
                'data': {
                    'type': 'comment',
                    'attributes': {
                    }
                }
            }
        )
        assert resp.status == HTTP_UNPROCESSABLE_ENTITY
        assert resp.json['code'] == "entity_error"
        assert resp.json['errors']['data']['attributes']['comment'][0] == "Brak danych w wymaganym polu."

    def test_invalid_resources_comment(self, removed_resource, draft_resource, client14):
        invalid_resource = Resource()
        invalid_resource.id = removed_resource.id + 100
        for resource in [invalid_resource, removed_resource, draft_resource]:
            resp = client14.simulate_post(
                path=f'/resources/{resource.id}/comments',
                json={
                    'data': {
                        'type': 'comment',
                        'attributes': {
                            'comment': "some valid\ncomment"
                        }
                    }
                }
            )

            assert resp.status == HTTP_NOT_FOUND
            assert resp.json['code'] == 'error'
            assert resp.json['title'] == '404 Not Found'
