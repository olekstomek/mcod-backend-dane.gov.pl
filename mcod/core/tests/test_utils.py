import datetime
import io
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable
from unittest.mock import MagicMock, patch
from xml.dom.minidom import parseString

import gevent
import pandas as pd
import pytest
from django.test import override_settings
from pyexpat import ExpatError
from pytest_mock import MockerFixture
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from mcod.core import tracker_patch
from mcod.core.utils import (
    CSVW,
    CSVWriter,
    FileMeta,
    XmlTextInvalid,
    XMLWriter,
    clean_columns_in_dataframe,
    create_rdf_graph_from_csv_content,
    disable_modeltracker,
    get_file_content_from_url,
    get_file_metadata,
    prepare_error_folder,
    save_df_to_xlsx,
)


class TestCleanColumnsInDataframe:
    def test_clean_single_column(self):
        df = pd.DataFrame({"ColumnName1": [" Value1 ", "Value2", None, "Value3 "], "ColumnName2": [0, 10, 20, 30]})

        cleaned_df: pd.DataFrame = clean_columns_in_dataframe(df, "ColumnName1").reset_index(drop=True)
        expected_df = pd.DataFrame({"ColumnName1": [" Value1 ", "Value2", "Value3 "], "ColumnName2": [0, 10, 30]})
        pd.testing.assert_frame_equal(cleaned_df, expected_df)

    def test_clean_multiple_columns(self):
        df = pd.DataFrame(
            {"ColumnName1": [" Value1 ", "Value2", None, "Value3 "], "ColumnName2": [" Value4", "   ", "", "Value5"]}
        )

        cleaned_df: pd.DataFrame = clean_columns_in_dataframe(df, "ColumnName1", "ColumnName2").reset_index(drop=True)
        expected_df = pd.DataFrame({"ColumnName1": [" Value1 ", "Value3 "], "ColumnName2": [" Value4", "Value5"]})
        pd.testing.assert_frame_equal(cleaned_df, expected_df)

    def test_non_existent_column(self):
        df = pd.DataFrame({"ColumnName1": ["Value1", "Value2", "Value3"], "ColumnName2": [10, 20, 30]})
        cleaned_df: pd.DataFrame = clean_columns_in_dataframe(df, "NonExistentColumn")
        pd.testing.assert_frame_equal(df, cleaned_df)


def test_save_df_to_xlsx_smoke():
    data = {"Column1": [1, 2, 3], "Column2": ["4", "5", "6"], "Column3": [7, "8 ", None]}
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir, "file_name.xlsx")
        # Given
        assert not temp_file_path.exists()
        # When
        save_df_to_xlsx(df, temp_file_path)
        # Then
        assert temp_file_path.exists()


def test_get_file_metadata_with_existing_file_returns_expected_size_and_tzinfo(tmp_path):
    file = tmp_path / "sample.txt"
    content = "hello world"
    file.write_text(content)
    meta = get_file_metadata(file)

    assert isinstance(meta, FileMeta)
    assert meta.size == len(content)
    assert isinstance(meta.created, datetime.datetime)
    assert isinstance(meta.modified, datetime.datetime)
    assert isinstance(meta.accessed, datetime.datetime)
    assert meta.created.tzinfo == datetime.timezone.utc
    assert meta.modified.tzinfo == datetime.timezone.utc
    assert meta.accessed.tzinfo == datetime.timezone.utc


def test_get_file_metadata_respects_custom_timezone(tmp_path):
    file = tmp_path / "sample.txt"
    file.write_text("abc")
    tz = datetime.timezone(datetime.timedelta(hours=2))
    meta = get_file_metadata(file, tz_info=tz)

    assert meta.created.tzinfo == tz
    assert meta.modified.tzinfo == tz
    assert meta.accessed.tzinfo == tz


def test_get_file_metadata_empty_file_has_zero_size(tmp_path):
    file = tmp_path / "empty.txt"
    file.touch()
    meta = get_file_metadata(file)

    assert meta.size == 0


def test_get_file_metadata_raises_for_missing_file(tmp_path):
    file = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        get_file_metadata(file)


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


def test_csv_writer_processes_data_lazily():
    """
    Verify that CSVWriter does not consume the entire generator into memory.
    The test tracks the sequence of events to ensure interleaved execution:
    Generate -> Write -> Generate -> Write.
    """
    # 1. Setup metadata and tracking
    headers = ["first_name", "last_name"]
    execution_trace = []

    # 2. Setup the "Spy" File
    # We mock the write method to log every time the CSV writer sends data to the file
    mock_file = MagicMock()

    def mock_write_side_effect(text: str):
        clean_text = text.strip()
        if clean_text:  # Ignore empty writes or just newlines if necessary
            execution_trace.append(f"DISK_WRITE: {clean_text}")

    mock_file.write.side_effect = mock_write_side_effect

    # 3. Setup the Lazy Generator
    # This generator logs exactly when a row is produced
    def data_generator() -> Iterable[Dict[str, Any]]:
        for i in range(2):
            execution_trace.append(f"GEN_ROW_{i}")
            yield {"first_name": f"Name{i}", "last_name": f"Surname{i}"}

    # 4. Execute the save method
    writer = CSVWriter(headers=headers, delimiter=";")
    writer.save(mock_file, data_generator())

    # 5. Assert the Interleaved Sequence
    # If the writer wasn't lazy, all GEN_ROW entries would appear before DISK_WRITE entries
    expected_sequence = [
        "DISK_WRITE: first_name;last_name",  # Header written first
        "GEN_ROW_0",  # Row 0 generated
        "DISK_WRITE: Name0;Surname0",  # Row 0 written to disk immediately
        "GEN_ROW_1",  # Row 1 generated
        "DISK_WRITE: Name1;Surname1",  # Row 1 written to disk immediately
    ]

    assert execution_trace == expected_sequence, f"Execution was not lazy! Trace received: {execution_trace}"


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


_XML_EXC = (ExpatError, XmlTextInvalid, UnicodeEncodeError)


@pytest.mark.parametrize(
    "char, expected_serialized, expect_error",
    [
        # ---- ALLOWED (should pass) ----
        ("&", "&amp;", None),
        ("<", "&lt;", None),
        (">", "&gt;", None),
        ('"', '"', None),
        ("'", "'", None),
        ("-", "-", None),
        ("*", "*", None),
        ("\u00A0", "\u00A0", None),  # non-breaking space
        ("\u200B", "\u200B", None),  # zero-width space
        ("😀", "😀", None),  # emoji
        ("\x85", "\x85", None),  # NEL (C1) — allowed in non-STRICT
        ("\U0010FFFF", "\U0010FFFF", None),  # highest valid code point — OK
        ("&#x26;", "&amp;#x26;", None),  # numeric entity treated literally (no unescape)
        ("&#x02;", "&amp;#x02;", None),  # numeric entity treated literally (no unescape)
        # ---- DISALLOWED (should raise) ----
        ("\x02", None, _XML_EXC),  # Start of Text (control char)
        ("\x00", None, _XML_EXC),  # NULL
        ("\x0B", None, _XML_EXC),  # Vertical Tab
        ("\x0C", None, _XML_EXC),  # Form Feed
    ],
)
def test_xml_writer_characters(mocker: MockerFixture, char, expected_serialized, expect_error):
    def new_callable(parent):
        data = {"new_tag": "tag"}
        return data.get(parent, "item")

    mocker.patch.object(XMLWriter, "custom_item_func", wraps=new_callable)

    data = {"new_tag": ["some_data", f"some_data2{char}"]}
    xml_file = io.StringIO()
    writer = XMLWriter()

    if expect_error:
        with pytest.raises(expect_error):
            writer.save(file_object=xml_file, data=data)
        return

    writer.save(file_object=xml_file, data=data)
    output = xml_file.getvalue()

    expected_xml = (
        f'<?xml version="1.0" encoding="UTF-8" ?>'
        f"<catalog>"
        f"<new_tag>"
        f"<tag>some_data</tag>"
        f"<tag>some_data2{expected_serialized}</tag>"
        f"</new_tag>"
        f"</catalog>"
    ).encode("utf-8")

    assert output == parseString(expected_xml).toprettyxml()


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
        writer.save(file_object=xml_file, data=data, language_catalog_path=str(tmp_path))

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


def test_xml_writer_error_dump(tmp_path, mocker):
    mocker.patch.object(XMLWriter, "custom_item_func", side_effect=lambda p: {"new_tag": "tag"}.get(p, "item"))
    data = {"new_tag": ["ok", "\uD800"]}
    xml_file = io.StringIO()
    writer = XMLWriter()

    mocker.patch("mcod.core.utils.prepare_error_folder", return_value=str(tmp_path))

    with pytest.raises(_XML_EXC):
        writer.save(xml_file, data, language_catalog_path=str(tmp_path))

    dump = tmp_path / "data.json"
    assert dump.exists()
    assert dump.read_text().startswith("{")


class TestCsvToRdfGraphStructure:
    def test_has_table_group(self, graph_3_rows: Graph):
        table_groups = list(graph_3_rows.subjects(RDF.type, CSVW.TableGroup))
        assert len(table_groups) == 1

    def test_has_table(self, graph_3_rows: Graph):
        tables = list(graph_3_rows.subjects(RDF.type, CSVW.Table))
        assert len(tables) == 1

    def test_table_has_correct_url(self, graph_3_rows: Graph, example_csv_file_url: str):
        tables = list(graph_3_rows.subjects(RDF.type, CSVW.Table))
        table_url = graph_3_rows.value(tables[0], CSVW.url)
        assert table_url == URIRef(example_csv_file_url)

    def test_table_group_links_to_table(self, graph_3_rows: Graph):
        table_group = list(graph_3_rows.subjects(RDF.type, CSVW.TableGroup))[0]
        table = list(graph_3_rows.subjects(RDF.type, CSVW.Table))[0]
        assert (table_group, CSVW.table, table) in graph_3_rows


class TestCsvToRdfGraphRows:
    def test_correct_number_of_rows(self, graph_3_rows: Graph):
        rows = list(graph_3_rows.subjects(RDF.type, CSVW.Row))
        assert len(rows) == 3

    def test_row_numbers(self, graph_3_rows: Graph):
        rows = list(graph_3_rows.subjects(RDF.type, CSVW.Row))
        row_nums = {int(graph_3_rows.value(r, CSVW.rownum)) for r in rows}
        assert row_nums == {1, 2, 3}

    def test_row_urls_contain_correct_rows_urls(self, graph_3_rows: Graph, example_csv_file_url: str):
        rows = list(graph_3_rows.subjects(RDF.type, CSVW.Row))
        row_urls = {str(graph_3_rows.value(r, CSVW.url)) for r in rows}
        assert row_urls == {
            f"{example_csv_file_url}#row=2",
            f"{example_csv_file_url}#row=3",
            f"{example_csv_file_url}#row=4",
        }

    def test_each_row_has_describes(self, graph_3_rows: Graph):
        rows = list(graph_3_rows.subjects(RDF.type, CSVW.Row))
        for row in rows:
            assert graph_3_rows.value(row, CSVW.describes) is not None


class TestCsvToRdfGraphData:
    def test_data_node_has_all_columns(self, graph_3_rows: Graph, example_csv_file_url: str):
        rows = list(graph_3_rows.subjects(RDF.type, CSVW.Row))
        for row in rows:
            data_node = graph_3_rows.value(row, CSVW.describes)
            predicates = {str(p) for p in graph_3_rows.predicates(data_node)}
            for col in ["Lp", "aaa", "bbb", "ccc"]:
                assert f"{example_csv_file_url}#{col}" in predicates

    def test_first_row_data_values(self, graph_3_rows: Graph, example_csv_file_url: str):
        rows = list(graph_3_rows.subjects(RDF.type, CSVW.Row))
        row1 = next(r for r in rows if graph_3_rows.value(r, CSVW.rownum) == Literal(1))
        data_node = graph_3_rows.value(row1, CSVW.describes)

        assert graph_3_rows.value(data_node, URIRef(f"{example_csv_file_url}#Lp")) == Literal("1")
        assert graph_3_rows.value(data_node, URIRef(f"{example_csv_file_url}#aaa")) == Literal("aaa1")
        assert graph_3_rows.value(data_node, URIRef(f"{example_csv_file_url}#bbb")) == Literal("bbb1")
        assert graph_3_rows.value(data_node, URIRef(f"{example_csv_file_url}#ccc")) == Literal("ccc1")


class TestCsvToRdfGraphEdgeCases:
    def test_only_header_row(self, example_csv_file_url: str):
        csv_content = "Lp,aaa,bbb,ccc\n"
        g = create_rdf_graph_from_csv_content(csv_content, example_csv_file_url)
        rows = list(g.subjects(RDF.type, CSVW.Row))
        assert rows == []
        assert len(list(g.subjects(RDF.type, CSVW.TableGroup))) == 1
        assert len(list(g.subjects(RDF.type, CSVW.Table))) == 1

    def test_completely_empty_file(self, example_csv_file_url: str):
        csv_content = ""
        with pytest.raises(ValueError) as exc:
            create_rdf_graph_from_csv_content(csv_content, example_csv_file_url)
        assert "CSV content is empty or has no headers." == str(exc.value)


def test_get_file_content_from_url_returns_decoded_content():
    mock_response = MagicMock()
    mock_response.read.return_value = b"Lp,aaa,bbb,ccc\n1,aaa1,bbb1,ccc1\n2,aaa2,bbb2,ccc2\n3,aaa3,bbb3,ccc3\n"

    with patch("mcod.core.utils.urlopen", return_value=mock_response) as mock_urlopen:
        result = get_file_content_from_url("https://example.com/test.csv")

    mock_urlopen.assert_called_once_with("https://example.com/test.csv")
    assert result == "Lp,aaa,bbb,ccc\n1,aaa1,bbb1,ccc1\n2,aaa2,bbb2,ccc2\n3,aaa3,bbb3,ccc3\n"


class TestDisableModelTracker:
    # TODO: To be removed with the flag S72_disable_modeltracker_in_local_context.be
    @pytest.fixture(autouse=True)
    def enable_s72_flag(self, monkeypatch):
        monkeypatch.setattr("mcod.core.utils.is_enabled", lambda _: True)

    def test_tracker_exists_after_db_load(self, resource_comment):
        model = resource_comment.__class__
        with disable_modeltracker():
            loaded = model.objects.get(pk=resource_comment.pk)
        assert hasattr(loaded, "_tracker")

    def test_tracker_is_not_disabled_after_context(self, resource_comment):
        model = resource_comment.__class__
        with disable_modeltracker():
            model.objects.get(pk=resource_comment.pk)
        loaded = model.objects.get(pk=resource_comment.pk)
        assert hasattr(loaded, "_tracker")

    def test_disable_modeltracker_does_not_call_original_set_saved_fields(self, resource_comment):
        model = resource_comment.__class__
        with patch.object(
            tracker_patch,
            "_original_set_saved_fields",
            wraps=tracker_patch._original_set_saved_fields,
        ) as original:
            with disable_modeltracker():
                model.objects.get(pk=resource_comment.pk)
        original.assert_not_called()

    def test_original_set_saved_fields_called_without_context(self, resource_comment):
        model = resource_comment.__class__
        with patch.object(
            tracker_patch,
            "_original_set_saved_fields",
            wraps=tracker_patch._original_set_saved_fields,
        ) as original:
            model.objects.get(pk=resource_comment.pk)
        original.assert_called_once()

    def test_disable_modeltracker_is_context_local(self, resource_comment):
        model = resource_comment.__class__

        def disabled():
            with disable_modeltracker():
                model.objects.get(pk=resource_comment.pk)

        def normal():
            model.objects.get(pk=resource_comment.pk)

        with patch.object(
            tracker_patch,
            "_original_set_saved_fields",
            wraps=tracker_patch._original_set_saved_fields,
        ) as original:
            jobs = [
                gevent.spawn(disabled),
                gevent.spawn(normal),
            ]
            gevent.joinall(jobs)

        original.assert_called()
