from unittest.mock import MagicMock

import pytest
from rdflib import Graph

from mcod.core.tests.fixtures import *  # noqa
from mcod.core.utils import create_rdf_graph_from_csv_content


def mocked_response(content: bytes) -> MagicMock:
    mock = MagicMock()
    mock.read.return_value = content
    return mock


@pytest.fixture
def graph_3_rows(example_csv_file_url) -> Graph:
    CSV_3_ROWS = "Lp,aaa,bbb,ccc\n1,aaa1,bbb1,ccc1\n2,aaa2,bbb2,ccc2\n3,aaa3,bbb3,ccc3\n"
    return create_rdf_graph_from_csv_content(CSV_3_ROWS, example_csv_file_url)


@pytest.fixture
def example_csv_file_url() -> str:
    return "https://api.mcod.local/media/resources/test.csv"
