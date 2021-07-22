import pytest
from django.core.files import File
from pytest_bdd import given, parsers, then

from mcod.core.tests.fixtures import *  # noqa
from mcod.core.tests.fixtures.bdd.common import prepare_file
from mcod.resources.archives import UnsupportedArchiveError
from mcod.resources.file_validation import analyze_resource_file
from mcod.resources.models import Chart, Resource


@given('I have buzzfeed resource with tabular data')
def tabular_resource(buzzfeed_fakenews_resource):
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
    resource.file = File(open(prepare_file('buzzfeed-logo.jpg'), 'rb'))
    resource.file.open('rb')
    resource.dataset = dataset
    resource.save()
    return resource


@pytest.fixture
def private_chart(buzzfeed_fakenews_resource, active_editor):
    chart = Chart()
    chart.chart = ["private chart"]
    chart.resource = buzzfeed_fakenews_resource
    chart.created_by = active_editor
    chart.modified_by = active_editor
    chart.save()
    return chart


@pytest.fixture
def default_chart(buzzfeed_fakenews_resource, active_editor):
    chart = Chart()
    chart.is_default = True
    chart.chart = ["default chart"]
    chart.resource = buzzfeed_fakenews_resource
    chart.created_by = active_editor
    chart.modified_by = active_editor
    chart.save()
    return chart


@then(parsers.parse('file is validated and result is {resource_file_format}'))
def file_format(validated_file, resource_file_format):
    extension, file_info, encoding, path, file_mimetype = analyze_resource_file(validated_file)
    assert extension == resource_file_format


@then(parsers.parse('file is validated and UnsupportedArchiveError is raised'))
def file_validation_exception(validated_file):
    with pytest.raises(UnsupportedArchiveError):
        analyze_resource_file(validated_file)


@then(parsers.parse('resource field {r_field} is {r_value}'))
def resource_field_value_is(context, r_field, r_value):
    resource = Resource.objects.latest('id')
    assert getattr(resource, r_field) == r_value


@then(parsers.parse('all list items should be of type {item_type}'))
def valid_items_type(context, item_type):
    for item in context.response.json['data']:
        assert item['type'] == item_type
