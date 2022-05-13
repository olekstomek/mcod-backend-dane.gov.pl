from pydoc import locate

from django.conf import settings


def test_xml_schema_deserialization(harvester_decoded_xml_1_2_data, harvester_xml_expected_data, institution):
    schema_path = settings.HARVESTER_IMPORTERS['xml']['SCHEMA']
    schema_class = locate(schema_path)
    schema = schema_class(many=True)
    schema.context['organization'] = institution
    items = schema.load(harvester_decoded_xml_1_2_data)
    assert items == harvester_xml_expected_data


def test_ckan_schema_deserialization(harvester_ckan_data, harvester_ckan_expected_data):
    schema_path = settings.HARVESTER_IMPORTERS['ckan']['SCHEMA']
    schema_class = locate(schema_path)
    schema = schema_class(many=True)
    items = schema.load(harvester_ckan_data)
    item = items[0]
    orig_organization_values = item.pop('organization').values()
    orig_resources_values = item.get('resources')[0].values()
    orig_scnd_resources_values = item.pop('resources')[1].values()
    expected_organization = harvester_ckan_expected_data.pop('organization')
    expected_resources = harvester_ckan_expected_data.get('resources')[0]
    expected_scnd_resources = harvester_ckan_expected_data.pop('resources')[1]
    assert list(item.keys()) == list(harvester_ckan_expected_data.keys())
    assert list(item.values()) == list(harvester_ckan_expected_data.values())
    assert all([itm in orig_resources_values for itm in expected_resources.values()])
    assert all([itm in orig_scnd_resources_values for itm in expected_scnd_resources.values()])
    assert all([itm in orig_organization_values for itm in expected_organization.values()])
    assert len(expected_organization.values()) == len(orig_organization_values)
    assert len(expected_resources.values()) == len(orig_resources_values)


def test_dcat_schema_deserialization(harvester_dcat_data, harvester_dcat_expected_data):
    schema_path = settings.HARVESTER_IMPORTERS['dcat']['SCHEMA']
    schema_class = locate(schema_path)
    schema = schema_class(many=True)
    deserialized_data = schema.load(harvester_dcat_data)
    deserialized_item = deserialized_data[0]
    deserialized_item['categories'].sort()
    deserialized_item['tags'].sort(key=lambda obj: obj['lang'])
    deserialized_item['resources'].sort(key=lambda obj: obj['ext_ident'])
    harvester_dcat_expected_data['categories'].sort()
    harvester_dcat_expected_data['tags'].sort(key=lambda obj: obj['lang'])
    assert harvester_dcat_expected_data == deserialized_item
