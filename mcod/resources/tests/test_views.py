# import os
# from time import sleep
# from urllib.parse import urlparse
#
# from falcon import HTTP_OK
#
# from mcod.core.tests.helpers.elasticsearch import ElasticCleanHelper
#
#
# class TestResourceView(ElasticCleanHelper):
#     def test_valid_get(self, es, db, client, resource_with_file, settings):
#         o = urlparse(settings.API_URL)
#         resp = client.simulate_get(
#             f'/resources/{resource_with_file.id}',
#             host=o.netloc, protocol=o.scheme
#         )
#         assert HTTP_OK == resp.status
#         assert 'attributes' in resp.json['data']
#         assert 'file_size' in resp.json['data']['attributes']
#         file_size = os.path.getsize(resource_with_file.file.path)
#         assert resp.json['data']['attributes']['file_size'] == file_size
#
#     def test_list_view(self, es, db, client, resources, settings):
#         o = urlparse(settings.API_URL)
#         resp = client.simulate_get('/resources',
#                                    host=o.netloc, protocol=o.scheme
#                                    )
#         assert HTTP_OK == resp.status
#         body = resp.json
#
#         for key in ('data', 'links', 'meta'):
#             assert key in body
#         assert type(body['data']) is list
#         assert len(body['data']) == len(resources)
#
#     def test_show_tabular_view(self, client, resource_with_file, resource, settings):
#         # Extra time for elasticsearch
#         o = urlparse(settings.API_URL)
#         assert resource_with_file.show_tabular_view
#         assert resource_with_file.data_is_valid is True
#         resp = client.simulate_get(
#             f'/resources/{resource_with_file.id}/data',
#             host=o.netloc, protocol=o.scheme
#         )
#         assert len(resp.json['data']['attributes']['headers']) == 4
#         assert len(resp.json['data']['attributes']['data']) == 6
#         for line in resp.json['data']['attributes']['data']:
#             assert len(line) == 4
#
#         resource_with_file.show_tabular_view = False
#         resource_with_file.save()
#         resp = client.simulate_get(f'/resources/{resource_with_file.id}/data')
#         assert resp.json['data'] is None
#
#         assert resource.data_is_valid is False
#         resp = client.simulate_get(f'/resources/{resource.id}/data')
#         assert resp.json['data'] is None

import pytest
from falcon import HTTP_OK

from mcod import settings


@pytest.mark.elasticsearch
def test_links_to_indexed_data(client14, tabular_resource):
    response = client14.simulate_get(f'/resources/{tabular_resource.id}')
    assert HTTP_OK == response.status
    body = response.json
    assert 'relationships' in body['data']
    assert 'tabular_data' in body['data']['relationships']
    assert 'links' in body['data']['relationships']['tabular_data']
    assert 'related' in body['data']['relationships']['tabular_data']['links']
    link = body['data']['relationships']['tabular_data']['links']['related']
    assert link == f'{settings.API_URL}/1.4/resources/{tabular_resource.id}/data'

    response = client14.simulate_get(f'/resources/?id={tabular_resource.id}')
    assert HTTP_OK == response.status
    body = response.json
    data = body['data'][0]
    assert 'relationships' in data
    assert 'tabular_data' in data['relationships']
    assert 'links' in data['relationships']['tabular_data']
    assert 'related' in data['relationships']['tabular_data']['links']
    link = data['relationships']['tabular_data']['links']['related']
    assert link == f'{settings.API_URL}/1.4/resources/{tabular_resource.id}/data'


@pytest.mark.elasticsearch
def test_links_to_no_data_resource(client14, no_data_resource):
    response = client14.simulate_get(f'/resources/{no_data_resource.id}')
    assert HTTP_OK == response.status
    body = response.json
    assert 'relationships' in body['data']
    assert 'tabular_data' not in body['data']['relationships']
    assert 'geo_data' not in body['data']['relationships']
