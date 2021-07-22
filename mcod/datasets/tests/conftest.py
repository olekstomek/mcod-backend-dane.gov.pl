import pytest

from pytest_bdd import given, then, parsers
from mcod.core.tests.fixtures import *  # noqa
from mcod.datasets.documents import DatasetDocumentActive
from mcod.resources.models import Resource
from mcod.resources.file_validation import analyze_resource_file
from mcod.resources.archives import UnsupportedArchiveError


@then('datasets list in response is sorted by <sort>')
def datasets_list_in_response_is_sorted_by(context, sort):
    data = context.response.json['data']
    if 'title' in sort:
        order = 'desc' if sort.startswith('-') else 'asc'
        field = sort[1:] if sort.startswith('-') else sort
        sort = {field: {'order': order, 'nested': {'path': 'title'}}}
    _sorted = DatasetDocumentActive().search().filter('term', status='published').sort(sort)[:len(data)]
    items = [int(x['id']) for x in data]
    sorted_items = [x.id for x in _sorted]
    assert items == sorted_items


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


@given('dataset with tabular resource')
def dataset_with_tabular_resource(buzzfeed_fakenews_resource):
    return buzzfeed_fakenews_resource.dataset


@given('dataset with remote file resource')
def dataset_with_remote_file_resource(remote_file_resource):
    return remote_file_resource.dataset


@given('dataset with local file resource')
def dataset_with_local_file_resource(local_file_resource):
    return local_file_resource.dataset
