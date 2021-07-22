import pytest
from mcod.resources.factories import ResourceFactory


@pytest.mark.elasticsearch
def test_headers_only_csv_file_validation(onlyheaders_csv_file):
    resource = ResourceFactory.create(
        type='file',
        format='csv',
        link=None,
        file=onlyheaders_csv_file,
    )
    assert resource.data_tasks.count() == 1
    assert 'zero-data-rows' in resource.data_tasks.order_by('id').last().result
    resource.revalidate()
    assert resource.data_tasks.count() == 2
    assert 'zero-data-rows' in resource.data_tasks.order_by('id').last().result
