from collections import namedtuple

import falcon
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from mcod import settings
from mcod.core.caches import flush_sessions
from mcod.lib.jwt import get_auth_header, decode_jwt_token


User = get_user_model()


@pytest.fixture()
def fake_user():
    return namedtuple('User', 'email state fullname')


@pytest.fixture()
def fake_session():
    return namedtuple('Session', 'session_key')


class TestLogout(object):

    def test_logout_by_not_logged_in(self, client):
        resp = client.simulate_post(path='/auth/logout')
        assert resp.status == falcon.HTTP_401
        assert resp.json['code'] == 'token_missing'

    def test_logout(self, client, active_user):
        flush_sessions()
        resp = client.simulate_post(path='/auth/login', json={
            'data': {
                'type': 'user',
                'attributes': {
                    'email': active_user.email,
                    'password': '12345.Abcde',
                }
            }
        })
        assert resp.status == falcon.HTTP_200

        active_usr_token = resp.json['data']['attributes']['token']
        auth_header = '%s %s' % (settings.JWT_HEADER_PREFIX, active_usr_token)
        session_valid = active_user.check_session_valid(auth_header)
        assert session_valid is True

        active_user2 = User.objects.create_user('test-active2@example.com', '12345.Abcde')
        active_user2.state = 'active'
        active_user2.save()

        resp = client.simulate_post(path='/auth/login', json={
            'data': {
                'type': 'user',
                'attributes': {
                    'email': active_user2.email,
                    'password': '12345.Abcde',
                }
            }
        })

        assert resp.status == falcon.HTTP_200

        active_usr2_token = resp.json['data']['attributes']['token']
        session_valid = active_user.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_usr_token))
        assert session_valid is True
        session_valid = active_user2.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_usr2_token))
        assert session_valid is True

        resp = client.simulate_post(path='/auth/logout', headers={
            "Authorization": "Bearer %s" % active_usr_token
        })

        assert resp.status == falcon.HTTP_200
        session_valid = active_user.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_usr_token))
        assert session_valid is False
        session_valid = active_user2.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_usr2_token))
        assert session_valid is True

        resp = client.simulate_post(path='/auth/logout', headers={
            "Authorization": "Bearer %s" % active_usr2_token
        })

        assert resp.status == falcon.HTTP_200
        session_valid = active_user.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_usr_token))
        assert session_valid is False
        session_valid = active_user2.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_usr2_token))
        assert session_valid is False


class TestProfile(object):

    def test_get_profile_after_logout(self, client, active_user):
        resp = client.simulate_post(path='/auth/login', json={
            'data': {
                'type': 'user',
                'attributes': {
                    'email': active_user.email,
                    'password': '12345.Abcde',
                }
            }
        })

        assert resp.status == falcon.HTTP_200
        token = resp.json['data']['attributes']['token']

        resp = client.simulate_post(path='/auth/logout', headers={
            "Authorization": "Bearer %s" % token
        })

        assert resp.status == falcon.HTTP_200

        resp = client.simulate_get(path='/auth/user', headers={
            "Authorization": "Bearer %s" % token
        })
        assert resp.status == falcon.HTTP_401
        assert resp.json['code'] == 'authentication_error'


class TestResetPasswordConfirm(object):

    def test_password_change(self, client, active_user):
        data = {
            'new_password1': '123.4.bce',
            'new_password2': '123.4.bce'
        }
        token = active_user.password_reset_token
        url = '/auth/password/reset/%s' % token

        resp = client.simulate_post(url, json=data)
        assert resp.status == falcon.HTTP_422
        assert 'new_password1' in resp.json['errors']

        data = {
            'new_password1': '123.4.bCe',
            'new_password2': '123.4.bCe!'
        }

        resp = client.simulate_post(url, json=data)
        assert resp.status == falcon.HTTP_422
        assert 'new_password1' in resp.json['errors']

        valid_data = {
            'new_password1': '123.4.bCe',
            'new_password2': '123.4.bCe'
        }

        resp = client.simulate_post(url, json=valid_data)
        assert resp.status == falcon.HTTP_200
        usr = User.objects.get(pk=active_user.id)
        assert usr.check_password(valid_data['new_password1']) is True
        t = usr.tokens.filter(token=token).first()
        assert t is not None
        assert t.is_valid is False

    def test_invalid_expired_token(self, client, active_user):
        data = {
            'new_password1': '123.4.bcE',
            'new_password2': '123.4.bcE'
        }

        token = active_user.password_reset_token

        token_obj = active_user.tokens.filter(token=token).first()

        assert token_obj.is_valid is True

        token_obj.invalidate()

        assert token_obj.is_valid is False

        url = '/auth/password/reset/%s' % token

        resp = client.simulate_post(url, json=data)
        assert resp.status == falcon.HTTP_400
        assert resp.json['code'] == 'expired_token'


class TestVerifyEmail(object):

    def test_pending_user(self, client, inactive_user):
        token = inactive_user.email_validation_token
        resp = client.simulate_get(path='/auth/registration/verify-email/%s/' % token)
        assert resp.status == falcon.HTTP_200

        usr = User.objects.get(email=inactive_user)
        assert usr.state == 'active'
        token_obj = usr.tokens.filter(token=token).first()
        assert token_obj.is_valid is False
        assert usr.email_confirmed.date() == timezone.now().date()

    def test_blocked_user(self, client, blocked_user):
        token = blocked_user.email_validation_token
        resp = client.simulate_get(path='/auth/registration/verify-email/%s/' % token)
        assert resp.status == falcon.HTTP_200

        usr = User.objects.get(email=blocked_user)
        assert usr.state == 'blocked'
        token_obj = usr.tokens.filter(token=token).first()
        assert token_obj.is_valid is False
        assert usr.email_confirmed.date() == timezone.now().date()

    def test_errors(self, client, inactive_user):
        resp = client.simulate_get(path='/auth/registration/verify-email/abcdef')
        assert resp.status == falcon.HTTP_404

        resp = client.simulate_get(path='/auth/registration/verify-email/8c37fd0c-5600-4277-a13a-67ced4a61e66')
        assert resp.status == falcon.HTTP_404

        v = inactive_user.email_validation_token
        token = inactive_user.tokens.filter(token=v).first()
        assert token.is_valid is True

        token.invalidate()

        resp = client.simulate_get(path='/auth/registration/verify-email/%s' % v)
        assert resp.status == falcon.HTTP_400


class TestAdminPanelAccess(object):

    def test_extended_permissions(self, active_user):
        header = get_auth_header(
            active_user,
            '1'
        )

        payload = decode_jwt_token(header)
        assert payload['user']['roles'] == []

        active_user.is_staff = True

        header = get_auth_header(
            active_user,
            '1'
        )

        payload = decode_jwt_token(header)
        assert payload['user']['roles'] == ['editor']

        active_user.is_staff = False
        active_user.is_superuser = True

        header = get_auth_header(
            active_user,
            '1'
        )

        payload = decode_jwt_token(header)
        assert payload['user']['roles'] == ['admin']


def test_admin_autocomplete_view_for_superuser(admin, active_editor):
    client = Client()
    client.force_login(admin)

    response = client.get(reverse("admin-autocomplete"))

    assert len(response.json()['results']) == 1
    assert response.json()['results'][0]['id'] == str(admin.id)
    assert response.json()['results'][0]['text'] == admin.email


def test_admin_autocomplete_view_for_not_superuser(admin, active_editor):
    client = Client()
    client.force_login(active_editor)

    response = client.get(reverse("admin-autocomplete"))

    assert len(response.json()['results']) == 0
