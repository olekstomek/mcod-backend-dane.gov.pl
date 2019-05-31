import pytest
from falcon import HTTP_200, HTTP_401


@pytest.mark.django_db
class TestSearchHistoriesApi():

    def test_for_not_authorized_user(self, hundred_of_search_histories, client):
        resp = client.simulate_get('/searchhistories')

        assert resp.status == HTTP_401

    def test_for_authorized_user_without_searchhistories(self, hundred_of_search_histories, admin_user, client):
        resp = client.simulate_post(path='/auth/login', json={
            'email': admin_user.email,
            'password': 'Britenet.1'
        })

        assert resp.status == HTTP_200
        active_usr_token = resp.json['data']['attributes']['token']
        resp = client.simulate_get('/searchhistories', headers={"Authorization": "Bearer %s" % active_usr_token})
        assert len(resp.json['data']) == 0

    def test_for_authorized_user_with_searchhistories(self, searchhistory_for_admin, admin_user, client):
        resp = client.simulate_post(path='/auth/login', json={
            'email': admin_user.email,
            'password': 'Britenet.1'
        })

        assert len(searchhistory_for_admin) == 5
        assert resp.status == HTTP_200
        active_usr_token = resp.json['data']['attributes']['token']
        resp = client.simulate_get('/searchhistories', headers={"Authorization": "Bearer %s" % active_usr_token})
        assert len(resp.json['data']) == 5

    def test_for_user_trying_to_get_sh_for_other_user(self, searchhistory_for_admin,
                                                      hundred_of_search_histories,
                                                      admin_user, client):
        other_user = hundred_of_search_histories[0].user

        resp = client.simulate_post(path='/auth/login', json={
            'email': admin_user.email,
            'password': 'Britenet.1'
        })

        assert resp.status == HTTP_200
        active_usr_token = resp.json['data']['attributes']['token']
        resp = client.simulate_get('/searchhistories', query_string=f"user={other_user.id}",
                                   headers={"Authorization": "Bearer %s" % active_usr_token})
        assert len(resp.json['data']) == 0
