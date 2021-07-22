import pytest
from django.conf import settings
from falcon import HTTP_200, HTTP_201, HTTP_204, HTTP_401, HTTP_OK
from openapi_core import create_spec
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.validation.response.validators import ResponseValidator
from pytest_bdd import scenarios, then, when

import mcod.unleash
from mcod.api import app
from mcod.core.tests.helpers.openapi_wrappers import FalconOpenAPIWrapper
from mcod.core.utils import jsonapi_validator
from mcod.counters.tasks import save_counters
from mcod.resources.models import Resource
from mcod.settings.test import API_URL

mcod.unleash.is_enabled = lambda x: True


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


@then('counter incrementing task is executed')
def counter_incrementing_task_is_executed(es, db):
    save_counters()


@when('I search in tabular data rows')
def setup_query(buzzfeed_fakenews_resource, context):
    context.api.path = '/resources/{}/data'.format(buzzfeed_fakenews_resource.id)


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
    assert 'title' in resp.json['meta']['headers_map'].values()
    assert 'published_date' in resp.json['meta']['headers_map'].values()
    assert resp.json['meta']['headers_map']['col4'] == 'published_date'
    assert len(resp.json['meta']['data_schema']['fields']) == 6
    links = resp.json['links']
    assert len(links) == 4
    assert links['self'] == 'http://api.test.mcod/resources/{}/data?page=1'.format(_rid)
    assert links['first'] == 'http://api.test.mcod/resources/{}/data?page=1'.format(_rid)
    assert links['last'] == 'http://api.test.mcod/resources/{}/data?page=50'.format(_rid)
    assert links['next'] == 'http://api.test.mcod/resources/{}/data?page=2'.format(_rid)


scenarios("features/resources_list_api.feature")
scenarios("features/tabular_view_test.feature")
scenarios("features/resource_details_api.feature")
scenarios('features/resource_comment.feature')


@pytest.mark.elasticsearch
def test_tabular_data_api14(buzzfeed_fakenews_resource, client14, mocker):
    _rid = buzzfeed_fakenews_resource.id

    resp = client14.simulate_get('/resources/{}/data/spec/1.4'.format(_rid))
    assert HTTP_OK == resp.status
    spec = create_spec(resp.json)

    # Test tabular data format
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
    # assert data['id'] == 'b97a04f7-2549-590e-b9ac-821ed67342fd' # obsolete.
    assert data['id'] == 'a20713b6-2a0b-582e-b1c2-75a095bace86'
    assert data['meta']['row_no'] == 2
    assert data['attributes']['col3']['val'] == '2,290,000.00'
    assert data['relationships']['resource']['data']['id'] == str(_rid)

    assert resp.json['meta']['count'] == 1000
    assert len(resp.json['meta']) == 9
    assert len(resp.json['meta']['headers_map']) == 6
    assert 'title' in resp.json['meta']['headers_map'].values()
    assert 'published_date' in resp.json['meta']['headers_map'].values()
    assert resp.json['meta']['headers_map']['col4'] == 'published_date'
    assert len(resp.json['meta']['data_schema']['fields']) == 6
    links = resp.json['links']
    assert len(links) == 3
    assert links['self'] == 'http://api.test.mcod/resources/{}/data?page=1'.format(_rid)
    assert links['last'] == 'http://api.test.mcod/resources/{}/data?page=50'.format(_rid)
    assert links['next'] == 'http://api.test.mcod/resources/{}/data?page=2'.format(_rid)

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
    assert links['self'] == 'http://api.test.mcod/resources/{}/data?per_page=25&q=col5%3ACrime&page=1'.format(
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
    assert validated_data[0]['col3']['val'] == '4347'
    assert validated_data[0]['col5']['val'] == 'Norwegian Lawmakers'
    links = resp.json['links']
    assert len(links) == 1
    assert 'self' in links

    resp = client14.simulate_get('/resources/{}/data'.format(_rid),
                                 query_string='q=col4.date:[2018-12-01 TO *]&per_page=10&page=2')
    assert HTTP_OK == resp.status
    valid, validated_data, errors = jsonapi_validator(resp.json)
    assert valid is True
    assert len(validated_data) == 10
    meta = resp.json['meta']
    assert meta['count'] == 61
    links = resp.json['links']
    assert len(links) == 5
    assert links[
        'first'] == 'http://api.test.mcod/resources/{}/' \
        'data?page=1&per_page=10&q=col4.date%3A%5B2018' \
        '-12-01%20TO%20%2A%5D'.format(_rid)
    assert links[
        'next'] == 'http://api.test.mcod/resources/{}/' \
        'data?page=3&per_page=10&q=col4.date%3A%5B2018' \
        '-12-01%20TO%20%2A%5D'.format(_rid)
    assert links[
        'prev'] == 'http://api.test.mcod/resources/{}/' \
        'data?page=1&per_page=10&q=col4.date%3A%5B2018' \
        '-12-01%20TO%20%2A%5D'.format(_rid)
    assert links[
        'last'] == 'http://api.test.mcod/resources/{}/' \
        'data?page=7&per_page=10&q=col4.date%3A%5B2018' \
        '-12-01%20TO%20%2A%5D'.format(_rid)
    assert links[
        'self'] == 'http://api.test.mcod/resources/{}/' \
        'data?page=2&per_page=10&q=col4.date%3A%5B2018' \
        '-12-01%20TO%20%2A%5D'.format(_rid)

    row_id = validated_data[0]['id']
    # Test single row
    req = FalconOpenAPIWrapper(
        app,
        method='GET',
        path='/resources/{}/data/{}'.format(_rid, row_id),
        path_params={
            'id': row_id
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
    assert len(validated_data) == 10
    assert validated_data[
        'col1']['val'] == 'Mums across Britain preparing to strum one off over CBeebies Bedtime Story tonight'
    assert validated_data['resource']['id'] == str(_rid)
    data = resp.json['data']
    assert data['type'] == 'row'
    assert data['meta']['row_no'] == 357
    assert data['relationships']['resource']['data']['id'] == str(_rid)
    meta = resp.json['meta']
    assert len(meta) == 7
    assert len(meta['headers_map']) == 6
    assert 'title' in meta['headers_map'].values()
    assert 'published_date' in meta['headers_map'].values()
    assert meta['headers_map']['col4'] == 'published_date'
    assert len(meta['data_schema']['fields']) == 6

    links = resp.json['links']
    assert len(links) == 1
    assert links[
        'self'] == 'http://api.test.mcod/resources/{}/' \
        'data/{}'.format(_rid, row_id)


@pytest.mark.elasticsearch
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


@pytest.mark.elasticsearch
def test_dates_in_detail_views(buzzfeed_fakenews_resource, client):
    _rid = buzzfeed_fakenews_resource.id

    assert buzzfeed_fakenews_resource.data_date is not None
    resp = client.simulate_get('/resources/{}/'.format(_rid))

    assert HTTP_OK == resp.status
    for d_name in ['created', 'modified', 'verified']:
        assert d_name in resp.json['data']['attributes']

    rs = Resource.objects.get(pk=buzzfeed_fakenews_resource.id)

    assert resp.json['data']['attributes']['modified'] == rs.modified.strftime('%Y-%m-%dT%H:%M:%SZ')
    assert resp.json['data']['attributes']['created'] == rs.created.strftime('%Y-%m-%dT%H:%M:%SZ')
    assert resp.json['data']['attributes']['verified'] == rs.verified.strftime('%Y-%m-%dT%H:%M:%SZ')
    assert resp.json['data']['attributes']['data_date'] == rs.data_date.strftime('%Y-%m-%d')


def test_not_authorized_user_get_empty_data_if_there_is_no_default_chart(private_chart, client14):
    resp = client14.simulate_get(
        path=f"/resources/{private_chart.resource_id}/chart"
    )

    assert resp.status == HTTP_200
    assert resp.json['data'] is None


def test_not_authorized_user_get_default_chart(default_chart, private_chart, client):
    resp = client.simulate_get(
        path=f"/resources/{default_chart.resource_id}/chart"
    )

    assert resp.status == HTTP_OK
    assert resp.json['data']['attributes']['chart'] == ["default chart"]


def test_authorized_users_get_own_chart_even_if_default_is_created(
        default_chart, private_chart, active_editor, client):
    resp = client.simulate_post(path='/auth/login', json={
        'data': {
            'type': 'user',
            'attributes': {
                'email': active_editor.email,
                'password': '12345.Abcde',
            }
        }
    })

    assert resp.status == HTTP_200

    active_editor_token = resp.json['data']['attributes']['token']
    session_valid = active_editor.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_editor_token))

    assert session_valid is True

    resp = client.simulate_get(
        path=f"/resources/{default_chart.resource_id}/chart",
        headers={"Authorization": "Bearer %s" % active_editor_token}

    )

    assert resp.status == HTTP_OK
    assert resp.json['data']['attributes']['chart'] == ["private chart"]


def test_authorized_editor_get_default_chart_even_if_private_is_latest_when_edit_mode_is_enabled(
        default_chart, private_chart, active_editor, client):
    resp = client.simulate_post(path='/auth/login', json={
        'data': {
            'type': 'user',
            'attributes': {
                'email': active_editor.email,
                'password': '12345.Abcde',
            }
        }
    })

    assert resp.status == HTTP_200

    active_editor_token = resp.json['data']['attributes']['token']
    session_valid = active_editor.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_editor_token))

    assert session_valid is True

    resp = client.simulate_get(
        path=f"/resources/{default_chart.resource_id}/chart?editor=t",
        headers={"Authorization": "Bearer %s" % active_editor_token}

    )

    assert resp.status == HTTP_OK
    # TODO: MCOD-1679 - which version should be returned after remove of editor parameter?
    # Is this test makes sense any longer?
    # assert resp.json['data']['attributes']['chart'] == str(["default chart"])
    assert resp.json['data']['attributes']['chart'] == ["private chart"]


def test_authorized_editor_get_default_chart_if_does_not_have_private(default_chart, active_editor, client):
    resp = client.simulate_post(path='/auth/login', json={
        'data': {
            'type': 'user',
            'attributes': {
                'email': active_editor.email,
                'password': '12345.Abcde',
            }
        }
    })

    assert resp.status == HTTP_200

    active_editor_token = resp.json['data']['attributes']['token']
    session_valid = active_editor.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_editor_token))

    assert session_valid is True

    resp = client.simulate_get(
        path=f"/resources/{default_chart.resource_id}/chart",
        headers={"Authorization": "Bearer %s" % active_editor_token}

    )

    assert resp.status == HTTP_OK
    assert resp.json['data']['attributes']['chart'] == ["default chart"]

# post


def test_not_authorized_user_cant_create_chart(client, buzzfeed_fakenews_resource):
    data = {
        "data": {
            "type": "chart",
            "attributes": {
                "resource_id": buzzfeed_fakenews_resource.id,
                "chart": {
                    "x": "col1",
                    "y": "col10"
                }
            }
        }
    }
    resp = client.simulate_post(
        path=f"/resources/{buzzfeed_fakenews_resource.id}/chart",
        json=data
    )
    assert resp.status == HTTP_401


def test_authorized_user_can_create_chart(client, buzzfeed_fakenews_resource, active_user):
    data = {
        "data": {
            "type": "chart",
            "attributes": {
                "chart": {
                    "x": "col1",
                    "y": "col10"
                }
            }
        }
    }

    resp = client.simulate_post(path='/auth/login', json={
        'data': {
            'type': 'user',
            'attributes': {
                'email': active_user.email,
                'password': '12345.Abcde',
            }
        }
    })

    assert resp.status == HTTP_200

    user_token = resp.json['data']['attributes']['token']
    session_valid = active_user.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, user_token))
    assert session_valid is True

    resp = client.simulate_post(
        path=f"/resources/{buzzfeed_fakenews_resource.id}/chart",
        headers={"Authorization": "Bearer %s" % user_token},
        json=data
    )
    assert resp.status == HTTP_201

# def test_authorized_user_second_private_chart_is_update(self, client, buzzfeed_fakenews_resource, active_user):
#     user_resource_chart = Chart.objects.filter(created_by=active_user, resource=buzzfeed_fakenews_resource)
#     assert len(user_resource_chart) == 0
#
#     # login
#     resp = client.simulate_post(path='/auth/login', json={
#         'email': active_user.email,
#         'password': '12345.Abcde'
#     })
#     assert resp.status == HTTP_200
#     user_token = resp.json['data']['attributes']['token']
#     session_valid = active_user.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, user_token))
#     assert session_valid is True
#
#     # create 1st
#     data1 = {
#         "data": {
#             "type": "chart",
#             "attributes": {
#                 "chart": {
#                     "x": "first",
#                 }
#             }
#         }
#     }
#     resp = client.simulate_post(
#         path=f"/resources/{buzzfeed_fakenews_resource.id}/chart",
#         headers={"Authorization": "Bearer %s" % user_token},
#         json=data1
#     )
#     assert resp.status == HTTP_201
#
#     user_resource_chart = Chart.objects.filter(created_by=active_user, resource=buzzfeed_fakenews_resource)
#     assert len(user_resource_chart) == 1
#
#     # create 2nd
#     data2 = {
#         "data": {
#             "type": "chart",
#             "attributes": {
#                 "resource_id": buzzfeed_fakenews_resource.id,
#                 "chart": {
#                     "x": "last",
#                 }
#             }
#         }
#     }
#     resp = client.simulate_post(
#         path=f"/resources/{buzzfeed_fakenews_resource.id}/chart",
#         headers={"Authorization": "Bearer %s" % user_token},
#         json=data2
#     )
#     assert resp.status == HTTP_201
#
#     user_resource_chart = Chart.objects.filter(created_by=active_user, resource=buzzfeed_fakenews_resource)
#     assert len(user_resource_chart) == 1
#
#     chart = Chart.objects.get(created_by=active_user, resource=buzzfeed_fakenews_resource)
#     assert chart.chart == {"x": "last"}

# def test_authorized_user_can_not_update_default_chart_when_create_chart(self, default_chart, active_user, client):
#     resp = client.simulate_post(path='/auth/login', json={
#         'email': active_user.email,
#         'password': '12345.Abcde'
#     })
#     assert resp.status == HTTP_200
#     user_token = resp.json['data']['attributes']['token']
#     session_valid = active_user.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, user_token))
#     assert session_valid is True
#
#     assert Chart.objects.filter(resource=default_chart.resource).count() == 1
#
#     # create 1st
#     data = {
#         "data": {
#             "type": "chart",
#             "attributes": {
#                 "chart": {
#                     "x": "first",
#                 }
#             }
#         }
#     }
#     resp = client.simulate_post(
#         path=f"/resources/{default_chart.resource.id}/chart",
#         headers={"Authorization": "Bearer %s" % user_token},
#         json=data
#     )
#     assert resp.status == HTTP_201
#     assert Chart.objects.filter(resource=default_chart.resource).count() == 2

# def test_authorized_editor_cant_create_default_chart_if_editor_is_not_in_params(
#         self, default_chart, active_editor, client):
#     active_editor.organizations.add(default_chart.resource.dataset.organization)
#     # login
#     resp = client.simulate_post(path='/auth/login', json={
#         'email': active_editor.email,
#         'password': '12345.Abcde'
#     })
#     assert resp.status == HTTP_200
#     user_token = resp.json['data']['attributes']['token']
#     session_valid = active_editor.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, user_token))
#     assert session_valid is True
#
#     assert Chart.objects.filter(resource=default_chart.resource).count() == 1
#
#     # create 1st
#     data = {
#         "data": {
#             "type": "chart",
#             "attributes": {
#                 "resource_id": default_chart.resource.id,
#                 "chart": {
#                     "x": "first",
#                 }
#             }
#         }
#     }
#     resp = client.simulate_post(
#         path=f"/resources/{default_chart.resource.id}/chart",
#         headers={"Authorization": "Bearer %s" % user_token},
#         json=data
#     )
#     assert resp.status == HTTP_201
#     assert resp.json['data']['attributes']['is_default'] is False
#     # create 1st
#     data = {
#         "data": {
#             "type": "chart",
#             "attributes": {
#                 "resource_id": default_chart.resource.id,
#                 "chart": {
#                     "x": "last",
#                 }
#             }
#         }
#     }
#     resp = client.simulate_post(
#         path=f"/resources/{default_chart.resource.id}/chart?editor=t",
#         headers={"Authorization": "Bearer %s" % user_token},
#         json=data
#     )
#     assert resp.status == HTTP_201
#     assert resp.json['data']['attributes']['is_default'] is True

# def test_authorized_user_which_is_not_editor_cant_create_default_chart(
#         self, client, buzzfeed_fakenews_resource, active_user):
#     data = {
#         "data": {
#             "type": "chart",
#             "attributes": {
#                 "chart": {
#                     "x": "col1",
#                     "y": "col10"
#                 }
#             }
#         }
#     }
#
#     assert not active_user.is_staff
#     assert not active_user.is_superuser
#
#     resp = client.simulate_post(path='/auth/login', json={
#         'email': active_user.email,
#         'password': '12345.Abcde'
#     })
#
#     assert resp.status == HTTP_200
#
#     user_token = resp.json['data']['attributes']['token']
#     session_valid = active_user.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, user_token))
#     assert session_valid is True
#
#     resp = client.simulate_post(
#         path=f"/resources/{buzzfeed_fakenews_resource.id}/chart?editor=t",
#         headers={"Authorization": "Bearer %s" % user_token},
#         json=data
#     )
#     assert resp.status == HTTP_401

# delete


def test_unauthorized_user_can_not_delete_chart(client, private_chart):
    resp = client.simulate_delete(
        path=f"/resources/charts/{private_chart.id}"
    )
    assert resp.status == HTTP_401


def test_authorized_editor_from_organization_can_delete_chart(
        default_chart, private_chart, active_editor, client):
    resp = client.simulate_post(path='/auth/login', json={
        'data': {
            'type': 'user',
            'attributes': {
                'email': active_editor.email,
                'password': '12345.Abcde',
            }
        }
    })

    assert resp.status == HTTP_200

    active_editor_token = resp.json['data']['attributes']['token']
    session_valid = active_editor.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_editor_token))
    active_editor.organizations.add(private_chart.resource.dataset.organization)
    assert session_valid is True

    resp = client.simulate_delete(
        path=f"/resources/charts/{private_chart.id}",
        headers={"Authorization": "Bearer %s" % active_editor_token}

    )

    assert resp.status == HTTP_204

# def test_authorized_editor_which_is_not_in_resource_dataset_organization_cant_delete_chart(
#         self, default_chart, private_chart, active_editor, client):
#     active_editor.organizations.clear()
#     assert not active_editor.organizations.all()
#
#     resp = client.simulate_post(path='/auth/login', json={
#         'email': active_editor.email,
#         'password': '12345.Abcde'
#     })
#
#     assert resp.status == HTTP_200
#
#     active_editor_token = resp.json['data']['attributes']['token']
#     session_valid = active_editor.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_editor_token))
#
#     assert session_valid is True
#
#     resp = client.simulate_delete(
#         path=f"/resources/charts/{private_chart.id}",
#         headers={"Authorization": "Bearer %s" % active_editor_token}
#     )
#
#     assert resp.status == HTTP_403


def test_remote_file_download_redirection(remote_file_resource, client):
    response = client.simulate_get(f'/resources/{remote_file_resource.id}/file')
    assert response.headers['location'].startswith('http://127.0.0.1')


def test_local_file_download_redirection(local_file_resource, client):
    response = client.simulate_get(f'/resources/{local_file_resource.id}/file')
    assert response.headers['location'].startswith(API_URL)
