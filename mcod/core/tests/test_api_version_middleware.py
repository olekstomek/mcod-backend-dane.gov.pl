"""
Tests mcod.core.api.middlewares.ApiVersionMiddleware - falcon api middleware.
"""

import pytest
from falcon import testing

_version_parameters = (
    ("1.0", 200),
    ("1.4", 200),
    ("1.1-rev0", 400),
)


@pytest.mark.parametrize("requested_version, expected_status_code", _version_parameters)
def test_version_middleware_in_header(client: testing.TestClient, requested_version: str, expected_status_code: int):
    response = client.simulate_get("/spec", headers={"X-API-VERSION": requested_version})
    assert response.status_code == expected_status_code, response


@pytest.mark.parametrize("requested_version, expected_status_code", _version_parameters)
def test_version_middleware_in_path(client: testing.TestClient, requested_version: str, expected_status_code: int):
    response = client.simulate_get(f"/{requested_version}/spec", headers={})
    assert response.status_code == expected_status_code, response
