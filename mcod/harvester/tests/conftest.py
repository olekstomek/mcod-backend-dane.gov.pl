from pytest_bdd import given, parsers, then

from mcod.core.tests.fixtures import *  # noqa
from mcod.harvester.factories import CKANDataSourceFactory, XMLDataSourceFactory
from mcod.harvester.models import DataSource


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
