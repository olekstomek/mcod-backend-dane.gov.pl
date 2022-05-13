import pytest
from django.core.files import File
from pytest_bdd import given, parsers, then

from mcod.core.tests.fixtures import *  # noqa
from mcod.core.tests.fixtures.bdd.common import prepare_file
from mcod.resources.models import Resource, ResourceFile


@given('I have buzzfeed resource with tabular data')
def tabular_resource(buzzfeed_fakenews_resource):
    buzzfeed_fakenews_resource = Resource.objects.get(pk=buzzfeed_fakenews_resource.pk)
    return buzzfeed_fakenews_resource


@given('I have resource with date and datetime')
def tabular_date_resource(resource_with_date_and_datetime):
    return resource_with_date_and_datetime


@then(parsers.parse('items count should be equal to {items_count:d}'))
def valid_items_count(context, tabular_resource, items_count):
    meta = context.response.json['meta']
    assert meta['count'] == items_count


@pytest.fixture
def table_resource_with_invalid_schema(dataset):
    resource = Resource()
    resource.url = "http://smth.smwhere.com"
    resource.title = "File resource name"
    resource.type = "file"
    resource.format = 'XLSX'
    resource.file = File(open(prepare_file('wrong_schema_table.xlsx'), 'rb'))
    resource.file.open('rb')
    resource.dataset = dataset
    resource.save()
    return resource


@pytest.fixture
def no_data_resource(dataset):
    resource = Resource()
    resource.title = "No data resource"
    resource.type = "file"
    resource.format = 'JPG'
    resource.dataset = dataset
    resource.save()
    ResourceFile.objects.create(
        file=File(open(prepare_file('buzzfeed-logo.jpg'), 'rb')),
        is_main=True,
        resource=resource,
        format='JPG'
    )
    resource = Resource.objects.get(pk=resource.pk)
    return resource


@then(parsers.parse('all list items should be of type {item_type}'))
def valid_items_type(context, item_type):
    for item in context.response.json['data']:
        assert item['type'] == item_type
