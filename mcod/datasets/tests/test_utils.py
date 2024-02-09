import io
import json
from pathlib import Path
from xml.dom.minidom import parseString

import pytest
from django.test import override_settings
from pyexpat import ExpatError
from pytest_mock import MockerFixture

from mcod.core.utils import CSVWriter, XMLWriter, prepare_error_folder


def test_csv_writer():
    """
    Test CSVWriter class save() method.
    Class should write data to given file.
    """
    data = [{"some header": "some value"}]
    writer = CSVWriter(headers=list(data[0].keys()))
    xml_file = io.StringIO()
    writer.save(data=data, file_object=xml_file)
    output = xml_file.getvalue()

    assert "some value" in output


def test_xml_writer(mocker: "MockerFixture"):
    """
    Validates 'XMLWriter' save functionality.

    Simulates a save operation using predefined data to verify that the generated XML
    content matches the expected XML structure defined in 'expected_output'.
    Performs a direct comparison of the generated XML output against the XML structure
    created with 'parseString' and 'toprettyxml'.

    Args:
    - mocker (MockerFixture): Pytest mocker fixture for mocking objects.
    """

    def new_callable(parent):
        data = {"new_tag": "tag"}
        return data.get(parent, "item")

    mocker.patch.object(XMLWriter, "custom_item_func", wraps=new_callable)

    data = {"new_tag": ["some_data", "some_data2"]}
    xml_file = io.StringIO()
    writer = XMLWriter()
    writer.save(file_object=xml_file, data=data)
    output = xml_file.getvalue()

    expected_output = (
        b'<?xml version="1.0" encoding="UTF-8" ?>'
        b"<catalog>"
        b"<new_tag>"
        b"<tag>some_data</tag>"
        b"<tag>some_data2</tag>"
        b"</new_tag>"
        b"</catalog>"
    )

    assert output == parseString(expected_output).toprettyxml()


def test_xml_writer_raise_exception(mocker: "MockerFixture", tmp_path: Path):
    """
    Validates 'XMLWriter' handling of illegal characters.

    Verifies that the 'XMLWriter' raises an 'ExpatError' when illegal characters
    are present in the data. Additionally, checks for the creation of a JSON file
    containing the data intended to be saved.

    Test Scenario:
    - Patches 'custom_item_func' to manage XML writing.
    - Sets up a temporary error folder using 'prepare_error_folder'.
    - Defines data with an illegal character ('\x02') in 'new_tag'.
    - Attempts data saving using 'XMLWriter', expecting an 'ExpatError'.
    - Verifies the creation of a JSON file with the intended data.

    Args:
    - mocker (MockerFixture): Pytest mocker fixture for object mocking.
    - tmp_path (path-like): Temporary directory provided by pytest for testing.
    """

    def new_callable(parent: str) -> str:
        xml_tags = {"new_tag": "tag"}
        return xml_tags.get(parent, "item")

    mocker.patch.object(XMLWriter, "custom_item_func", wraps=new_callable)
    mocker.patch("mcod.core.utils.prepare_error_folder", return_value=tmp_path)

    data = {"new_tag": ["some_data", "something\x02to_test"]}
    xml_file = io.StringIO()
    writer: XMLWriter = XMLWriter()
    with pytest.raises(ExpatError), override_settings(METADATA_MEDIA_ROOT=tmp_path):
        writer.save(
            file_object=xml_file, data=data, language_catalog_path=str(tmp_path)
        )

    expected_error_file_path = f"{tmp_path}/data.json"
    assert Path(expected_error_file_path).is_file()

    with open(expected_error_file_path, "r") as file:
        file_data = json.loads(file.read())
        assert file_data == data


def test_prepare_error_folder(tmp_path: Path):
    """
    Test to ensure 'prepare_error_folder' function operates as expected.

    It verifies the functionality of 'prepare_error_folder' by:
    - Creating a new folder 'parsing_errors' inside the temporary path.
    - Creating a file 'new_file.txt' inside the 'parsing_errors' folder.
    - Checking if 'prepare_error_folder' correctly manipulates the folder.

    The test validates that after invoking 'prepare_error_folder':
    - The old file 'new_file.txt' is removed from the 'parsing_errors' folder.
    - The function creates an empty folder, replacing the removed file.
    - The returned string path matches the path of the newly created empty folder.
    """
    new_folder_path = Path(tmp_path) / "parsing_errors"
    new_folder_path.mkdir()

    with open(f"{new_folder_path}/new_file.txt", "w") as f:
        f.write("some_text")

    str_path: str = prepare_error_folder(str(tmp_path))

    assert not Path(f"{new_folder_path}/new_file.txt").exists()
    assert str_path == str(new_folder_path)
    assert new_folder_path.exists()
