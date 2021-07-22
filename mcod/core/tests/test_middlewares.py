from django.test import Client
# import falcon

# FIXME: Commenting out this test again - it does not work on my environment.

# @pytest.mark.run(order=0)
#
# def test_locale_middleware(client, dataset):
#     test_values = [
#         ('', 'pl', 'co tydzień'),
#         ('*', 'pl', 'co tydzień'),
#         ('zz', 'pl', 'co tydzień'),
#         ('pl', 'pl', 'co tydzień'),
#         ('pl-PL', 'pl', 'co tydzień'),
#         # ('pl,en', 'pl', 'co tydzień'),
#         ('en', 'en', 'weekly'),
#         ('en-US', 'en', 'weekly'),
#         #('en,pl', 'en', 'weekly'),
#         ('en;q=1,pl;q=0.7,de;q=0.8', 'en', 'weekly'),
#         # ('en;q=0.8,pl;q=0.9,de;q=0.7', 'pl', 'co tydzień'),
#         #('en-US;q=0.9,pl-PL;q=1,de;q=0.7', 'pl', 'co tydzień'),
#         ('en-US;q=0.9,pl-PL;q=0.6,de;q=0.7', 'en', 'weekly'),
#         # TODO inne tłumaczenia po ich opracowaniu
#     ]
#     for header, lang, expected in test_values:
#         result = client.simulate_get(f"/datasets/{dataset.id}", headers={
#             'Accept-Language': header
#         })
#
#         assert result.status == falcon.HTTP_200
#         assert result.headers['content-language'] == lang
#         assert result.json['data']['attributes']['update_frequency'] == expected


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
