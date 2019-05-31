import pytest
import falcon

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from mcod.applications.models import Application as ApplicationModel
from mcod.histories.models import History
from mcod.core.tests.helpers.elasticsearch import ElasticCleanHelper

UserModel = get_user_model()


class TestApplicationFollowing(ElasticCleanHelper):

    @pytest.mark.django_db
    def test_unlogged_user(self, client, valid_application):
        resp = client.simulate_post(
            path=f'/applications/{valid_application.id}/follow'
        )
        assert falcon.HTTP_UNAUTHORIZED == resp.status
        assert resp.json['code'] == 'token_missing'

        resp = client.simulate_delete(
            path=f'/applications/{valid_application.id}/follow'
        )
        assert falcon.HTTP_UNAUTHORIZED == resp.status
        assert resp.json['code'] == 'token_missing'

        get_resp = client.simulate_get(f'/applications/{valid_application.id}')
        assert get_resp.json['data']['attributes']['followed'] is False

    @pytest.mark.django_db
    def test_logged_user(self, client, active_user, valid_application):
        # logowanie
        resp = client.simulate_post(
            path='/auth/login',
            json={
                'email': active_user.email,
                'password': 'Britenet.1'
            }
        )
        token = resp.json['data']['attributes']['token']

        # sprawdzenie czy aplikacja (świeża) nie jest obserwowana
        get_resp = client.simulate_get(
            f'/applications/{valid_application.id}',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_resp.json['data']['attributes']['followed'] is False

        # rozpoczęcie obserwacji
        resp = client.simulate_post(
            f'/applications/{valid_application.id}/follow',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert falcon.HTTP_OK == resp.status
        assert resp.json['data']['attributes']['followed'] is True

        # sprawdzenie aktualizacji listy
        app_db = ApplicationModel.objects.get(pk=valid_application.id)
        app_db.users_following.get(pk=active_user.id)

        get_resp = client.simulate_get(
            '/applications',
            query_string=f'id={valid_application.id}',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_resp.json['data'][0]['attributes']['followed'] is True

        # wycofanie z obserwacji
        resp = client.simulate_delete(
            f'/applications/{valid_application.id}/follow',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert falcon.HTTP_OK == resp.status
        assert resp.json['data']['attributes']['followed'] is False

        with pytest.raises(ObjectDoesNotExist):
            app_db.users_following.get(pk=active_user.id)

        user_db = UserModel.objects.get(pk=active_user.id)
        with pytest.raises(ObjectDoesNotExist):
            user_db.followed_applications.get(pk=valid_application.id)

        get_resp = client.simulate_get(
            '/applications',
            query_string=f'id={valid_application.id}',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_resp.json['data'][0]['attributes']['followed'] is False

    @pytest.mark.django_db
    def test_history_is_updated_after_create_history_and_proper_user_is_set(self, client, active_user,
                                                                            valid_application):
        # logowanie
        resp = client.simulate_post(
            path='/auth/login',
            json={
                'email': active_user.email,
                'password': 'Britenet.1'
            }
        )
        token = resp.json['data']['attributes']['token']

        # rozpoczęcie obserwacji
        resp = client.simulate_post(
            f'/applications/{valid_application.id}/follow',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert falcon.HTTP_OK == resp.status
        assert resp.json['data']['attributes']['followed'] is True

        last_history = History.objects.last()
        assert last_history.action == "INSERT"
        assert last_history.table_name == "user_following_application"
        assert last_history.change_user_id == active_user.id

        # wycofanie z obserwacji
        resp = client.simulate_delete(
            f'/applications/{valid_application.id}/follow',
            headers={"Authorization": f"Bearer {token}"}
        )
        assert falcon.HTTP_OK == resp.status
        assert resp.json['data']['attributes']['followed'] is False

        last_history = History.objects.last()
        assert last_history.action == "DELETE"
        assert last_history.table_name == "user_following_application"
        assert last_history.change_user_id == active_user.id
