from typing import Optional
from unittest.mock import Mock

import requests


def mocked_response(url: str, content: Optional[bytes], headers: Optional[dict]) -> requests.Response:
    mock_resp = Mock(spec=requests.Response)
    mock_resp.url = url
    mock_resp.content = content
    mock_resp.headers = headers
    return mock_resp
