import base64
from pathlib import Path

import pytest


@pytest.fixture
def valid_jpeg_bytes() -> bytes:
    image_path = Path(__file__).parents[4] / "data" / "test_samples" / "example.jpg"
    return image_path.read_bytes()


@pytest.fixture
def valid_jpeg_base64(valid_jpeg_bytes: bytes) -> str:
    return base64.b64encode(valid_jpeg_bytes).decode("ascii")


@pytest.fixture
def valid_jpeg_data_uri(valid_jpeg_base64: str) -> str:
    return "data:image/jpeg;base64," + valid_jpeg_base64


@pytest.fixture
def jpg_declared_jpeg_data_uri(valid_jpeg_base64: str) -> str:
    return "data:image/jpg;base64," + valid_jpeg_base64


@pytest.fixture
def jpe_declared_jpeg_data_uri(valid_jpeg_base64: str) -> str:
    return "data:image/jpe;base64," + valid_jpeg_base64


@pytest.fixture
def png_declared_jpeg_data_uri(valid_jpeg_base64: str) -> str:
    return "data:image/png;base64," + valid_jpeg_base64


@pytest.fixture
def url_quoted_text_data_uri() -> str:
    return "data:text/plain,hello%20world"


@pytest.fixture
def url_quoted_text_bytes() -> bytes:
    return b"hello world"


@pytest.fixture
def html_data_uri() -> str:
    return "data:text/html;base64,PGh0bWw+PHNjcmlwdD5hbGVydCgiWFNTIik8L3NjcmlwdD48L2h0bWw+"


@pytest.fixture
def non_image_png_data_uri() -> str:
    return "data:image/png;base64,bm90LWFuLWltYWdl"
