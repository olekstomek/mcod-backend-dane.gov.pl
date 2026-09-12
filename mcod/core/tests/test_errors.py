import falcon
import pytest

from mcod.lib.errors import error_serializer


class S1:
    def on_get(self, req, resp, **kwargs):
        exc = falcon.HTTPBadRequest(title="omg", description="all is not well")
        error_serializer(req, resp, exc)


class S_400:
    def on_get(self, req, resp, **kwargs):
        raise falcon.HTTPBadRequest(title="Ups, bad request", description="Malformed request")


class S_500:
    def on_get(self, req, resp, **kwargs):
        raise falcon.HTTPInternalServerError


class S_422:
    def on_get(self, req, resp, **kwargs):
        raise falcon.HTTPUnprocessableEntity


class S_422_with_int_key_errors:
    def on_get(self, req, resp, **kwargs):
        from webargs.falconparser import HTTPError

        raise HTTPError("422 Unprocessable Entity", errors={0: {"name": ["Required"]}, 1: {"url": ["Invalid"]}})


@pytest.fixture(scope="module")
def uri():
    return "/test_errors"


@pytest.mark.depends_on_component
@pytest.mark.component_api
class TestErrors:
    @pytest.mark.run(order=0)
    def test_error_serializer_10(self, client, uri):
        client.app.add_route(uri, S1())
        result = client.simulate_get(uri)
        assert result.status == falcon.HTTP_200
        assert result.json["title"] == "omg"
        assert result.json["description"] == "all is not well"
        assert result.headers["content-type"] == "application/json"
        assert result.headers["vary"] == "Accept"

    @pytest.mark.run(order=0)
    def test_400_10(self, client, uri):
        client.app.add_route(uri, S_400())
        result = client.simulate_get(uri)
        assert result.status == falcon.HTTP_400
        assert result.json["code"] == "error"
        assert result.json["title"] == "Ups, bad request"
        assert result.json["description"] == "Malformed request"

    @pytest.mark.run(order=0)
    def test_500_10(self, client, uri):
        client.app.add_route(uri, S_500())
        result = client.simulate_get(uri)
        assert result.json["code"] == "server_error"
        assert result.status == falcon.HTTP_500
        assert result.json["title"] == "Wystąpił nieoczekiwany błąd. Proszę, spróbuj później."

    @pytest.mark.run(order=0)
    def test_422_10(self, client, uri):
        client.app.add_route(uri, S_422())
        result = client.simulate_get(uri)
        assert result.status == falcon.HTTP_422
        assert result.json["code"] == "entity_error"
        assert result.json["title"] == "422 Unprocessable Entity"

    @pytest.mark.run(order=0)
    def test_400(self, client14, uri):
        client14.app.add_route(uri, S_400())
        result = client14.simulate_get(uri)
        assert result.status == falcon.HTTP_400
        assert len(result.json["errors"]) == 1
        error = result.json["errors"][0]
        assert error["code"] == "400_bad_request"

    @pytest.mark.run(order=0)
    def test_500(self, client14, uri):
        client14.app.add_route(uri, S_500())
        result = client14.simulate_get(uri)
        assert len(result.json["errors"]) == 1
        error = result.json["errors"][0]
        assert error["code"] == "500_internal_server_error"

    @pytest.mark.run(order=0)
    def test_422(self, client14, uri):
        client14.app.add_route(uri, S_422())
        result = client14.simulate_get(uri)
        assert len(result.json["errors"]) == 1
        error = result.json["errors"][0]
        assert error["code"] == "422_unprocessable_entity"

    @pytest.mark.run(order=0)
    def test_422_with_int_key_errors(self, client14, uri):
        client14.app.add_route(uri, S_422_with_int_key_errors())
        result = client14.simulate_get(uri)
        assert result.status == falcon.HTTP_422
        assert len(result.json["errors"]) == 2
        pointers = [err["source"]["pointer"] for err in result.json["errors"]]
        assert "/0/name" in pointers
        assert "/1/url" in pointers
