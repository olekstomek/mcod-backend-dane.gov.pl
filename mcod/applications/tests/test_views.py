import pytest
from falcon import HTTP_OK, HTTP_NOT_FOUND, HTTP_UNPROCESSABLE_ENTITY

from mcod.core.tests.helpers.elasticsearch import ElasticCleanHelper


@pytest.mark.django_db
class TestApplicationsView(ElasticCleanHelper):
    def test_noargs_get(self, client10, applications_list):
        resp = client10.simulate_get('/applications')
        assert HTTP_OK == resp.status
        body = resp.json
        for key in ('data', 'links', 'meta'):
            assert key in body
        assert type(body['data']) is list
        assert len(body['data']) == 3

        listed_apps = {app['id']: app for app in body['data']}
        for app in applications_list:
            if app.slug == 'app-del':
                assert app.id not in listed_apps
                continue
            assert app.id in listed_apps
            assert listed_apps[app.id]['attributes']['title'] == app.title
            assert listed_apps[app.id]['attributes']['slug'] == app.slug
            assert listed_apps[app.id]['attributes']['url'] == app.url

            assert listed_apps[app.id]['links']['self'] == f'/applications/{app.id},{app.slug}'
            assert listed_apps[app.id]['relationships']['datasets']['links']['related'][
                       'href'] == f'/applications/{app.id},{app.slug}/datasets'  # noqa
            assert listed_apps[app.id]['type'] == 'applications'

    def test_query_get(self, client10, applications_list):
        resp = client10.simulate_get('/applications', params={'q': 'application'})
        assert HTTP_OK == resp.status
        body = resp.json

        for key in ('data', 'links', 'meta'):
            assert key in body
        assert type(body['data']) is list
        assert len(body['data']) == 2
        titles = {app['attributes']['title'] for app in body['data']}
        assert 'Deleted application' not in titles
        assert 'Test name' not in titles


@pytest.mark.django_db
class TestApplicationView(object):
    def test_valid_get(self, client10, valid_application):
        resp = client10.simulate_get(f'/applications/{valid_application.id}')
        assert HTTP_OK == resp.status

        for key in ('data', 'links', 'meta'):
            assert key in resp.json

        data = resp.json['data']
        assert data['type'] == 'applications'
        assert data['id'] == valid_application.id

        attrs = valid_application.__dict__
        for key in ('_state', 'id', 'status', 'status_changed', 'is_removed', 'image',
                    'created_by_id', 'modified_by_id', '_monitor_status_changed',
                    'uuid'):
            del attrs[key]
        attrs['created'] = attrs['created'].isoformat().replace('T', ' ')
        attrs['modified'] = attrs['modified'].isoformat().replace('T', ' ')
        attrs['image_url'] = ''
        attrs['image_thumb_url'] = ''
        attrs['tags'] = []
        attrs['followed'] = False

        for key in data['attributes']:
            assert data['attributes'][key] == attrs[key]

        assert data['links']['self'] == f'/applications/{data["id"]},test-name'

    def test_get_invalid_id(self, client10, valid_application):
        resp = client10.simulate_get('/applications/!nV')
        assert HTTP_NOT_FOUND == resp.status

        resp = client10.simulate_get(f'/applications/{valid_application.id + 10}')
        assert HTTP_NOT_FOUND == resp.status

    def test_get_deleted(self, client10, valid_application):
        del_id = valid_application.id
        valid_application.delete()

        resp = client10.simulate_get(f'/applications/{del_id}')
        assert HTTP_NOT_FOUND == resp.status

    def test_thumbnail(self, client10, valid_application_with_logo):
        resp = client10.simulate_get(f'/applications/{valid_application_with_logo.id}')
        assert HTTP_OK == resp.status

        for key in ('data', 'links', 'meta'):
            assert key in resp.json

        assert 'data' in resp.json
        assert 'attributes' in resp.json['data']
        assert 'image_url' in resp.json['data']['attributes']
        assert 'image_thumb_url' in resp.json['data']['attributes']


@pytest.mark.django_db
class TestApplicationDatasetsView(object):
    def test_valid_get(self, client, valid_application):
        resp = client.simulate_get(f'/applications/{valid_application.id}/datasets')
        assert resp.status == HTTP_OK

        assert len(resp.json['data']) == 0
        # TODO dorobić fixture dataset dla valid_application i sprawdzic jego pola

        assert all((key in resp.json['links']) for key in ('first', 'self'))
        assert resp.json['links']['first'] == f'/applications/{valid_application.id}/datasets?page=1&per_page=20'
        assert resp.json['links']['first'] == resp.json['links']['self']


@pytest.mark.django_db
class TestApplicationProposalForm(object):
    minimal_json = {
        "title": "tytuł",
        "notes": "ble\nbleble\nala ma kota",
        # "author": "Someone Test",
        "url": "http://www.google.pl",
    }

    def test_valid_full_post(self, client):
        json = self.minimal_json.copy()
        json['applicant_email'] = 'anuone@anywhere.any'
        json["datasets"] = [1, 2, 3]
        json["image"] = "data:image/png;base64,SoMeBaSE64iMAge=="
        json["keywords"] = ["ala", "ma", "kota"]
        json['external_datasets'] = [
            {
                'title': 'wszystko',
                'url': 'http://google.com'
            },
            {
                'title': 'nic',
                'url': 'http://some.fake.url.any'
            },
        ]

        resp = client.simulate_post(
            path='/applications/suggest',
            json=json
        )

        assert resp.status == HTTP_OK
        assert resp.json == {}

    def test_valid_min_post(self, client):
        resp = client.simulate_post(
            path='/applications/suggest',
            json=self.minimal_json
        )

        assert resp.status == HTTP_OK
        assert resp.json == {}

    def test_missing_fields_posts(self, client):
        for key in self.minimal_json:
            json = self.minimal_json.copy()
            del json[key]

            resp = client.simulate_post(
                path='/applications/suggest',
                json=json
            )
            assert resp.status == HTTP_UNPROCESSABLE_ENTITY

    def test_invalid_email(self, client):
        json = self.minimal_json.copy()
        json['applicant_email'] = "invalid@mail"

        resp = client.simulate_post(
            path='/applications/suggest',
            json=json
        )
        assert resp.status == HTTP_UNPROCESSABLE_ENTITY

    def test_invalid_url(self, client):
        json = self.minimal_json.copy()
        json['url'] = "invalid[]url,^&*"

        resp = client.simulate_post(
            path='/applications/suggest',
            json=json
        )
        assert resp.status == HTTP_UNPROCESSABLE_ENTITY

    def test_invalid_datasets(self, client):
        json = self.minimal_json.copy()
        json['datasets'] = 'app is using all dataset'

        resp = client.simulate_post(
            path='/applications/suggest',
            json=json
        )
        assert resp.status == HTTP_UNPROCESSABLE_ENTITY

# @pytest.mark.django_db
# class TestApplicationHistoryView(object):
#     def test_valid_get(self, client, valid_application, valid_application2):
#         resp = client.simulate_get(f"/applications/{valid_application.id}/history")
#         assert resp.status == HTTP_OK
#         assert len(resp.json['data']) == 1
#         assert resp.json
#
#         old_url = valid_application.url
#         valid_application.url = new_url = "http://modified.app.com"
#         valid_application.save()
#         resp = client.simulate_get(f"/applications/{valid_application.id}/history")
#         assert resp.status == HTTP_OK
#         assert len(resp.json['data']) == 2
#         diff = resp.json['data'][0]['attributes']['difference']
#         assert set(diff['values_changed'].keys()) == {"root['url']", }
#         assert diff['values_changed']["root['url']"]['new_value'] == new_url
#         assert diff['values_changed']["root['url']"]['old_value'] == old_url
#
#         old_notes = valid_application.notes
#         valid_application.notes = new_notes = "Nowy opisik aplikacji"
#         valid_application.save()
#
#         valid_application2.url = "http://smth.smwheere.com"
#         valid_application2.notes = "Blablabla..."
#         valid_application2.save()
#
#         resp = client.simulate_get(f"/applications/{valid_application.id}/history")
#         assert resp.status == HTTP_OK
#         assert len(resp.json['data']) == 3
#         diff = resp.json['data'][0]['attributes']['difference']
#         assert set(diff['values_changed'].keys()) == {"root['notes']", }
#         assert diff['values_changed']["root['notes']"]['new_value'] == new_notes
#         assert diff['values_changed']["root['notes']"]['old_value'] == old_notes
