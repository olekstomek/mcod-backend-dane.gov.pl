import json
import os
import hashlib

from django.conf import settings
from django.test import Client
from pytest_bdd import given, parsers, then, when
from unittest.mock import patch
import requests_mock

from mcod.datasets.models import Dataset
from mcod.harvester.factories import CKANDataSourceFactory, XMLDataSourceFactory
from mcod.core.registries import factories_registry
from mcod.harvester.models import DataSource, DataSourceImport
from mcod.resources.models import Resource


@given(parsers.parse('CKAN datasource with id {obj_id:d} active'))
def active_ckan_datasource_with_id(obj_id):
    return CKANDataSourceFactory.create(pk=obj_id, status='active')


@given(parsers.parse('XML datasource with id {obj_id:d} active'))
def active_xml_datasource_with_id(obj_id):
    return XMLDataSourceFactory.create(pk=obj_id, status='active')


@given(parsers.parse('CKAN datasource with id {obj_id:d} inactive'))
def inactive_ckan_datasource_with_id(obj_id):
    return CKANDataSourceFactory.create(pk=obj_id, status='inactive')


@given(parsers.parse('XML datasource with id {obj_id:d} inactive'))
def inactive_xml_datasource_with_id(obj_id):
    return XMLDataSourceFactory.create(pk=obj_id, status='inactive')


@given(parsers.parse('datasource with id {obj_id:d} attribute {attr_name} is set to {attr_value}'))
def datasource_with_id_attribute_is(obj_id, attr_name, attr_value):
    attr_value = None if attr_value == 'None' else attr_value
    DataSource.objects.filter(id=obj_id).update(**{attr_name: attr_value})


@then(parsers.parse('datasource with id {obj_id:d} is activated and last_activation_date is updated'))
def datasource_with_id_activation(obj_id):
    obj = DataSource.objects.get(id=obj_id)
    obj.status = 'active'
    obj.save()
    assert obj.last_activation_date is not None


@then(parsers.parse('datasource with id {obj_id:d} is deactivated and last_activation_date is not updated'))
def datasource_with_id_deactivation(obj_id):
    obj = DataSource.objects.get(id=obj_id)
    assert obj.last_activation_date is None
    obj.status = 'inactive'
    obj.save()
    assert obj.last_activation_date is None


@given(parsers.parse('active {datasource_type} with id {obj_id:d} for data{data_str}'))
def active_datasource_by_type_for_data(datasource_type, obj_id, data_str):
    _factory = factories_registry.get_factory(datasource_type)
    data = json.loads(data_str)
    data['status'] = 'active'
    data['id'] = obj_id
    return _factory.create(**data)


@when(parsers.parse('ckan datasource with id {obj_id:d} finishes importing objects'))
@requests_mock.Mocker(kw='mock_request')
def datasource_finishes_import(obj_id, **kwargs):
    mock_request = kwargs['mock_request']
    obj = DataSource.objects.get(pk=obj_id)
    example_image_path = os.path.join(settings.TEST_SAMPLES_PATH, 'example.jpg')
    simple_csv_path = os.path.join(settings.TEST_SAMPLES_PATH, 'simple.csv')
    with open(simple_csv_path, 'rb') as tmp_file:
        mock_request.get('http://mock-resource.com.pl/simple.csv',
                         headers={'content-type': 'application/csv'}, content=tmp_file.read())
    mock_request.post(settings.SPARQL_UPDATE_ENDPOINT)
    ckan_data_path = os.path.join(settings.TEST_SAMPLES_PATH, 'harvester_ckan_import_example.json')
    with open(ckan_data_path, 'rb') as json_resp_data:
        mock_request.get(obj.api_url, headers={'content-type': 'application/json'}, content=json_resp_data.read())
    with patch('mcod.harvester.utils.urlretrieve') as mock_urlretrieve:
        mock_urlretrieve.return_value = example_image_path, {}
        obj.import_data()


@then(parsers.parse('ckan datasource with id {obj_id:d} created all data in db'))
def datasource_imported_resources(obj_id):
    dataset = Dataset.objects.get(source_id=obj_id)
    resources = Resource.objects.filter(dataset__source_id=obj_id).order_by('ext_ident')
    res = resources[0]
    second_res = resources[1]
    org = dataset.organization
    source_import = DataSourceImport.objects.get(datasource_id=obj_id)
    assert source_import.error_desc == ''
    assert source_import.status == 'ok'
    assert source_import.datasets_count == 1
    assert source_import.datasets_created_count == 1
    assert source_import.resources_count == 2
    assert source_import.resources_created_count == 2
    assert org.title == 'Wydział Środowiska'
    assert org.uuid.urn == 'urn:uuid:b97080cc-858d-4763-a751-4b54bf3fb0f0'
    assert dataset.title == 'Ilości odebranych odpadów z podziałem na sektory'
    assert dataset.notes == 'Wartości w tonach'
    assert dataset.license_chosen == 2
    assert res.title == 'Ilości odebranych odpadów z podziałem na sektory'
    assert res.ext_ident == '6db2e083-72b8-4f92-a6ab-678fc8461865'
    assert res.description == '##Sektory:'
    assert res.format == 'csv'
    assert second_res.title == 'Ilości odebranych odpadów z podziałem na sektory ze spacja'
    assert second_res.ext_ident == '6db2e083-72b8-4f92-a6ab-678fc8461866'


@when(parsers.parse('xml datasource with id {obj_id:d} of version {version} finishes importing objects'))
@requests_mock.Mocker(kw='mock_request')
def xml_datasource_finishes_import(
        obj_id, version, harvester_decoded_xml_1_2_import_data, harvester_decoded_xml_1_4_import_data,
        harvester_decoded_xml_1_5_import_data, **kwargs):
    mock_request = kwargs['mock_request']
    obj = DataSource.objects.get(pk=obj_id)
    simple_csv_path = os.path.join(settings.TEST_SAMPLES_PATH, 'simple.csv')
    with open(simple_csv_path, 'rb') as tmp_file:
        mock_request.get('http://mock-resource.com.pl/simple.csv',
                         headers={'content-type': 'application/csv'}, content=tmp_file.read())
    mock_request.post(settings.SPARQL_UPDATE_ENDPOINT)
    xml_data_path = os.path.join(settings.TEST_SAMPLES_PATH, 'harvester', f'import_example{version}.xml')
    with open(xml_data_path, 'rb') as xml_resp_data:
        xml_request_kwargs = {
            'url': obj.xml_url,
            'headers': {'content-type': 'application/xml'},
            'content': xml_resp_data.read()
        }

    mock_request.get(**xml_request_kwargs)
    md5_url = xml_request_kwargs['url'].replace('.xml', '.md5')
    mock_request.get(md5_url, content=hashlib.md5(xml_request_kwargs['content']).hexdigest().encode('utf-8'))
    mock_request.head(**xml_request_kwargs)
    xml_map = {
        '1.2': harvester_decoded_xml_1_2_import_data,
        '1.4': harvester_decoded_xml_1_4_import_data,
        '1.5': harvester_decoded_xml_1_5_import_data,
    }
    with patch('mcod.harvester.utils.urlretrieve') as mock_urlretrieve:
        with patch('mcod.harvester.utils.decode_xml') as mock_to_dict:
            mock_urlretrieve.return_value = xml_data_path, {}
            mock_to_dict.return_value = xml_map[version]
            obj.import_data()


@then(parsers.parse('xml datasource with id {obj_id:d} of version {version} created all data in db'))
def xml_datasource_imported_resources(obj_id, version):
    source_import = DataSourceImport.objects.get(datasource_id=obj_id)
    assert source_import.error_desc == ''
    assert source_import.status == 'ok'
    assert source_import.datasets_count == 1
    assert source_import.datasets_created_count == 1
    assert source_import.resources_count == 2
    assert source_import.resources_created_count == 2
    dataset = Dataset.objects.get(source_id=obj_id)
    res = Resource.objects.filter(dataset__source_id=obj_id)
    assert dataset.ext_ident == 'zbior_extId_1'
    assert dataset.title == 'Zbiór danych - nowy scheme CC0 1.0'
    assert dataset.notes == 'Opis w wersji PL - opis testowy do testow UAT'
    assert dataset.license_chosen == 1
    assert set(dataset.categories.values_list('code', flat=True)) == {'TRAN', 'ECON'}
    assert dataset.keywords_list == [{'name': '2028_tagPL', 'language': 'pl'}]
    assert set(res.values_list('ext_ident', flat=True)) == {'zasob_extId_zasob_1', 'zasob_extId_zasob_2'}
    assert set(res.values_list('title', flat=True)) == {'ZASOB CSV LOCAL', 'ZASOB csv REMOTE'}
    if version == '1.4':  # from this version special_signs of resources are imported also.
        for resource in res:
            assert resource.special_signs_symbols_list == '-'
    elif version == '1.5':  # from this version has_high_value_data, has_dynamic_data attrs are imported also.
        assert dataset.has_high_value_data
        assert dataset.has_dynamic_data
        assert set(res.values_list('has_dynamic_data', flat=True)) == {True, None}
        assert set(res.values_list('has_high_value_data', flat=True)) == {False, None}


@when(parsers.parse('dcat datasource with id {obj_id:d} finishes importing objects'))
@requests_mock.Mocker(kw='mock_request')
def dcat_datasource_finishes_import(obj_id, harvester_dcat_data, **kwargs):
    mock_request = kwargs['mock_request']
    obj = DataSource.objects.get(pk=obj_id)
    mock_request.get(obj.api_url,
                     headers={'content-type': 'application/rdf+xml'},
                     content=harvester_dcat_data.serialize())
    mock_request.post(settings.SPARQL_UPDATE_ENDPOINT)
    simple_csv_path = os.path.join(settings.TEST_SAMPLES_PATH, 'simple.csv')
    with open(simple_csv_path, 'rb') as tmp_file:
        mock_request.get('http://example-uri.com/distribution/999',
                         headers={'content-type': 'application/csv'}, content=tmp_file.read())
    obj.import_data()


@then(parsers.parse('dcat datasource with id {obj_id:d} created all data in db'))
def dcat_datasource_imported_resources(obj_id):
    source_import = DataSourceImport.objects.get(datasource_id=obj_id)
    assert source_import.error_desc == ''
    assert source_import.status == 'ok'
    assert source_import.datasets_count == 1
    assert source_import.datasets_created_count == 1
    assert source_import.resources_count == 2
    assert source_import.resources_created_count == 2
    dataset = Dataset.objects.get(source_id=obj_id)
    resources = Resource.objects.filter(dataset__source_id=obj_id).order_by('-ext_ident')
    res = resources[0]
    second_res = resources[1]
    assert res.title == 'Distribution title'
    assert res.description == 'Some distribution description'
    assert res.ext_ident == '999'
    assert second_res.title == 'Second distribution title'
    assert second_res.description == 'Some other distribution description'
    assert second_res.ext_ident == '1000'
    assert dataset.title == 'Dataset title'
    assert dataset.notes == 'DESCRIPTION'
    assert dataset.ext_ident == '1'
    assert set(dataset.categories.values_list('code', flat=True)) == {'ECON'}
    assert {'name': 'jakis tag', 'language': 'pl'} in dataset.keywords_list
    assert {'name': 'tagggg', 'language': 'en'} in dataset.keywords_list


@when(parsers.parse('admin\'s harvester page {page_url} is requested'))
@when('admin\'s harvester page <page_url> is requested')
@requests_mock.Mocker(kw='mock_request')
def admin_harvester_page_is_requested(admin_context, page_url, **kwargs):
    mock_request = kwargs['mock_request']
    client = Client()
    client.force_login(admin_context.admin.user)
    if admin_context.admin.method == 'POST':
        api_url = admin_context.obj['api_url']
        if isinstance(api_url, list):
            api_url = api_url[0]
        if 'ckan' in admin_context.obj['source_type']:
            mock_request.get(api_url, json={}, headers={'Content-Type': 'application/json'})
            mock_request.head(api_url, json={}, headers={'Content-Type': 'application/json'})
        response = client.post(page_url, data=getattr(admin_context, 'obj', None), follow=True)
    else:
        response = client.get(page_url, follow=True)
    admin_context.response = response
