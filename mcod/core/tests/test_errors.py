import falcon
import pytest

from mcod.lib.errors import error_serializer


class S1(object):
    def on_get(self, req, resp, **kwargs):
        exc = falcon.HTTPBadRequest(title='omg', description='all is not well')
        error_serializer(None, resp, exc)


class S_400(object):
    def on_get(self, req, resp, **kwargs):
        raise falcon.HTTPBadRequest(
            title='Ups, bad request',
            description='Malformed request'
        )


class S_500(object):
    def on_get(self, req, resp, **kwargs):
        raise falcon.HTTPInternalServerError


class S_422(object):
    def on_get(self, req, resp, **kwargs):
        raise falcon.HTTPUnprocessableEntity


@pytest.fixture(scope='module')
def uri():
    return '/test_errors'


class TestErrors(object):
    @pytest.mark.run(order=0)
    def test_error_serializer(self, client, uri):
        client.app.add_route(uri, S1())
        result = client.simulate_get(uri)
        assert result.status == falcon.HTTP_200
        assert result.json['title'] == 'omg'
        assert result.json['description'] == 'all is not well'
        assert result.headers['content-type'] == 'application/json'
        assert result.headers['vary'] == 'Accept'

    @pytest.mark.run(order=0)
    def test_400(self, client, uri):
        client.app.add_route(uri, S_400())
        result = client.simulate_get(uri)
        assert result.status == falcon.HTTP_400
        assert result.json['code'] == 'error'
        assert result.json['title'] == 'Ups, bad request'
        assert result.json['description'] == 'Malformed request'

    @pytest.mark.run(order=0)
    def test_500(self, client, uri):
        client.app.add_route(uri, S_500())
        result = client.simulate_get(uri)
        assert result.json['code'] == 'server_error'
        assert result.status == falcon.HTTP_500
        assert result.json['title'] == '500 Internal Server Error'

    @pytest.mark.run(order=0)
    def test_422(self, client, uri):
        client.app.add_route(uri, S_422())
        result = client.simulate_get(uri)
        assert result.status == falcon.HTTP_422
        assert result.json['code'] == 'entity_error'
        assert result.json['title'] == '422 Unprocessable Entity'
