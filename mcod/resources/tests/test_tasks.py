from unittest.mock import patch

import pytest

from mcod.resources.tasks import delete_es_resource_tabular_data_index


@pytest.mark.parametrize(
    "ids, deleted_indexes",
    [
        (20, ["resource-20"]),
        ([], []),
        ([30, 40, 50], ["resource-30", "resource-40", "resource-50"]),
    ],
)
def test_task_delete_es_resource_tabular_data_index(ids, deleted_indexes):
    """
    GIVEN one resource id or list of resource ids
    WHEN call `delete_es_resource_tabular_data_index` with these ids as parameter
    THEN function that deletes tabular data index will be called.
    """
    with patch("mcod.resources.tasks.delete_index", return_value=True) as mock_delete_index:
        delete_es_resource_tabular_data_index(ids)

        for delete_index in deleted_indexes:
            mock_delete_index.assert_any_call(delete_index)
