import pytest
from pytest_bdd import scenarios

scenarios(
    'features/task_results.feature',
)


@pytest.mark.elasticsearch
def test_headers_only_csv_file_validation(onlyheaderscsv_resource):
    assert onlyheaderscsv_resource.data_tasks.count() == 1
    assert 'zero-data-rows' in onlyheaderscsv_resource.data_tasks.order_by('id').last().result
    onlyheaderscsv_resource.revalidate()
    assert onlyheaderscsv_resource.data_tasks.count() == 2
    assert 'zero-data-rows' in onlyheaderscsv_resource.data_tasks.order_by('id').last().result
