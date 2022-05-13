from django.test import Client


def test_user_token_middleware(admin, settings):
    client = Client()

    resp = client.get("/")
    assert resp.status_code == 302
    assert settings.API_TOKEN_COOKIE_NAME not in resp.cookies

    client.force_login(admin)
    resp = client.get("/")
    assert resp.status_code == 200
    assert settings.API_TOKEN_COOKIE_NAME in resp.cookies

    client.get('/logout/')
    resp = client.get('/')
    assert resp.status_code == 302
    assert settings.API_TOKEN_COOKIE_NAME in resp.cookies
    assert resp.cookies[settings.API_TOKEN_COOKIE_NAME]['expires'] == 'Thu, 01 Jan 1970 00:00:00 GMT'
    # cookie will be deleted
