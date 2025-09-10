import pytest
from namedlist import namedlist

from mcod.lib.helpers import change_namedlist, validate_update_data_for_beat_schedule


class TestChangeNamedlist:
    def test_correct_change(self):
        test_list = namedlist("test_list", ["x", "y"])
        test_list_instance = test_list(1, 2)
        assert test_list_instance.x == 1
        assert test_list_instance.y == 2

        test_list_instance2 = change_namedlist(test_list_instance, {"x": 3})
        assert test_list_instance2.x == 3
        assert test_list_instance2.y == 2

    def test_assert(self):
        test_list = namedlist("test_list", ["x", "y"])
        test_list_instance = test_list(1, 2)
        with pytest.raises(KeyError) as e:
            change_namedlist(test_list_instance, {"z": 3})
        assert "Field with name z is not in list test_list(x=1, y=2)" in str(e.value)


@pytest.mark.parametrize(
    ["data_to_validate", "expected_result"],
    [
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":21, "hour": 23, "minute": 20}}',
            True,
            id="OK - 1 task data for change",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":21, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation":{"hour": 7, "minute": 5}}',
            True,
            id="OK - 2 tasks data for change",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":21, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation":{"hour": 7, "minute": 5}, "catalog_xml_file_creation":{"hour": 8, "minute": 10}}',
            False,
            id="One task duplicated in data_to_validate",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":21, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation_xxxxxxxxx":{"hour": 7, "minute": 5}}',
            False,
            id="task name not in beat_schedule",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"month_of_year": 13, "day_of_month":21, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation":{"hour": 7, "minute": 5}}',
            False,
            id="bad month_of_year value",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_week":8, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation":{"hour": 7, "minute": 5}}',
            False,
            id="bad day_of_week value",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":32, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation":{"hour": 7, "minute": 5}}',
            False,
            id="bad day_of_month value",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":21, "hour": 26, "minute": 20},'
            ' "catalog_xml_file_creation":{"hour": 7, "minute": 5}}',
            False,
            id="bad hour value",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":21, "hour": 23, "minute": 10},'
            ' "catalog_xml_file_creation":{"hour": 7, "minute": 85}}',
            False,
            id="bad minute value",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"doy_of_month":10, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation":{"hour": 7, "minute": 5}}',
            False,
            id="bad parameter name (doy_of_month)",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":10, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation":{"houur": 7, "minute": 5}}',
            False,
            id="bad parameter name (houur)",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":10, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation":{"hour": 7, "mminut": 5}}',
            False,
            id="bad parameter name (mminut)",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":10, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation":{"hour": 7, "minute": 5, "aaaa": 5}}',
            False,
            id="additional bad parameter name (aaaa)",
        ),
        pytest.param(
            '{"kronika_sparql_performance": {"day_of_month":10, "hour": 23, "minute": 20},'
            ' "catalog_xml_file_creation":{"hour": 7}}',
            True,
            id="time parameter without minute",
        ),
        pytest.param(
            "aaaabbbccc",
            False,
            id="not correct parameters structure - string",
        ),
        pytest.param(
            "{}",
            False,
            id="not correct parameters structure - empty dict",
        ),
        pytest.param(
            "[]",
            False,
            id="not correct parameters structure - empty list",
        ),
        pytest.param(
            "",
            False,
            id="not correct parameters structure - empty string",
        ),
    ],
)
def test_validate_update_data_for_beat_schedule(beat_schedule_fixture: dict, data_to_validate: str, expected_result: bool):
    assert validate_update_data_for_beat_schedule(beat_schedule_fixture, data_to_validate) == expected_result


def test_validate_update_data_for_beat_schedule_task_name_included_other_task_name(beat_schedule_fixture: dict):
    beat_schedule: dict = {**beat_schedule_fixture, "catalog_xml_file_creation_extended_name": {"hour": 8, "minute": 10}}
    data_to_validate: str = (
        '{"kronika_sparql_performance": {"day_of_month":21, "hour": 23, "minute": 20}, '
        '"catalog_xml_file_creation":{"hour": 7, "minute": 5}, '
        '"catalog_xml_file_creation_extended_name":{"hour": 12, "minute": 30}}'
    )
    assert validate_update_data_for_beat_schedule(beat_schedule, data_to_validate)
