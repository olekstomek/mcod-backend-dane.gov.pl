from time import sleep

import os
import pytest
from falcon import HTTP_OK
from mcod.core.tests.helpers.elasticsearch import ElasticCleanHelper


@pytest.mark.django_db
class TestResourceView(ElasticCleanHelper):
    def test_valid_get(self, client, valid_resource_with_file):
        resp = client.simulate_get(f'/resources/{valid_resource_with_file.id}')
        assert HTTP_OK == resp.status
        assert 'attributes' in resp.json['data']
        assert 'file_size' in resp.json['data']['attributes']
        file_size = os.path.getsize(valid_resource_with_file.file.path)
        assert resp.json['data']['attributes']['file_size'] == file_size

    def test_list_view(self, client, resource_list):
        resp = client.simulate_get('/resources')
        assert HTTP_OK == resp.status
        body = resp.json

        for key in ('data', 'links', 'meta'):
            assert key in body
        assert type(body['data']) is list
        assert len(body['data']) == len(resource_list)

    def test_show_tabular_view(self, client, valid_resource_with_file, valid_resource):
        # Extra time for elasticsearch
        sleep(5)
        assert valid_resource_with_file.show_tabular_view
        assert valid_resource_with_file.data_is_valid == 'SUCCESS'
        resp = client.simulate_get(f'/resources/{valid_resource_with_file.id}/data')
        assert len(resp.json['data']['attributes']['headers']) == 4
        assert len(resp.json['data']['attributes']['data']) == 6
        for line in resp.json['data']['attributes']['data']:
            assert len(line) == 4

        valid_resource_with_file.show_tabular_view = False
        valid_resource_with_file.save()
        resp = client.simulate_get(f'/resources/{valid_resource_with_file.id}/data')
        assert resp.json['data'] is None

        assert valid_resource.data_is_valid == 'NOT_AVAILABLE'
        resp = client.simulate_get(f'/resources/{valid_resource.id}/data')
        assert resp.json['data'] is None
