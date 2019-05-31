import smtplib
from collections import namedtuple

import falcon
import os
import pytest
import shutil
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from mcod import settings
from mcod.core.caches import flush_sessions
from mcod.lib.jwt import get_auth_header, decode_jwt_token
from mcod.users.depricated.serializers import LoginSerializer, RegistrationSerializer

User = get_user_model()


@pytest.fixture()
def fake_user():
    return namedtuple('User', 'email state fullname')


@pytest.fixture()
def fake_session():
    return namedtuple('Session', 'session_key')


class TestLogin(object):
    @pytest.mark.django_db
    def test_active_user_login(self, client, active_user):
        resp = client.simulate_post(path='/auth/login', json={
            'email': active_user.email,
            'password': 'Britenet.1'
        })

        assert resp.status == falcon.HTTP_200
        data = resp.json
        # data['data']['attributes']['_document_meta'] = {}
        # result = LoginSerializer().validate(data)
        assert LoginSerializer().validate(data) == {}

    @pytest.mark.django_db
    def test_login_email_is_case_insensitive(self, client, editor_user):
        resp = client.simulate_post(path='/auth/login', json={
            'email': editor_user.email.upper(),
            'password': 'Britenet.1'
        })

        assert resp.status == falcon.HTTP_200
        assert LoginSerializer().validate(resp.json) == {}

    def test_wrong_body(self, client):
        resp = client.simulate_post(path='/auth/login')
        assert resp.status == falcon.HTTP_422

        resp = client.simulate_post(path='/auth/login', json={
            'password': 'secret_password'
        })
        assert resp.status == falcon.HTTP_422

        resp = client.simulate_post(path='/auth/login', json={
            'aaaaa': 'bbbbb'
        })

        assert resp.status == falcon.HTTP_422

    @pytest.mark.django_db
    def test_wrong_email(self, client):
        resp = client.simulate_post(path='/auth/login', json={
            'email': 'doesnotexist@example.com',
            'password': 'Britenet.1'
        })

        assert resp.status == falcon.HTTP_401
        assert resp.json['code'] == 'account_not_exist'

        for email in ['aaa', 'aaa@', '@aaa', 'aaa@aaa']:
            resp = client.simulate_post(path='/auth/login', json={
                'email': email,
                'password': 'Britenet.1'
            })

            assert resp.status == falcon.HTTP_422
            assert resp.json['code'] == 'entity_error'

    @pytest.mark.django_db
    def test_wrong_password(self, client, active_user):
        resp = client.simulate_post(path='/auth/login', json={
            'email': active_user.email,
            'password': 'Britenet.15'
        })

        assert resp.status == falcon.HTTP_401
        assert resp.json['code'] == 'authorization_error'

        resp = client.simulate_post(path='/auth/login', json={
            'email': active_user.email,
            'password': 'abcd'
        })

        assert resp.status == falcon.HTTP_401
        assert resp.json['code'] == 'authorization_error'

    @pytest.mark.django_db
    def test_pending_user(self, client, inactive_user):
        req_data = {
            'email': inactive_user.email,
            'password': 'Britenet.1'
        }
        resp = client.simulate_post(path='/auth/login', json=req_data)
        assert resp.status == falcon.HTTP_403
        assert resp.json['code'] == 'account_inactive'

    @pytest.mark.django_db
    def test_deleted_user(self, client, deleted_user):
        req_data = {
            'email': deleted_user.email,
            'password': 'Britenet.1'
        }
        resp = client.simulate_post(path='/auth/login', json=req_data)
        assert resp.status == falcon.HTTP_403
        assert resp.json['code'] == 'account_inactive'

    @pytest.mark.django_db
    def test_blocked_user(self, client, blocked_user):
        req_data = {
            'email': blocked_user.email,
            'password': 'Britenet.1'
        }
        resp = client.simulate_post(path='/auth/login', json=req_data)
        assert resp.status == falcon.HTTP_401
        assert resp.json['code'] == 'account_unavailable'

    def test_unknown_state_user(self, client, fake_user, fake_session, mocker):
        usr = fake_user(
            email='test@example.com', state='unknown_state', fullname='Test Example'
        )
        mocker.patch('mcod.users.views.login')
        mocker.patch('mcod.users.views.session_store', return_value=fake_session(
            session_key=1234
        ))

        mocker.patch('mcod.users.views.User.objects.get', return_value=usr)

        mocker.patch('mcod.users.views.authenticate', return_value=usr)

        req_data = {
            'email': 'test@example.com',
            'password': 'secret_password'
        }

        resp = client.simulate_post(path='/auth/login', json=req_data)
        assert resp.status == falcon.HTTP_401
        assert resp.json['code'] == 'account_unavailable'


class TestRegistration(object):
    @pytest.mark.django_db
    def test_required_fields(self, client):
        req_data = {
            'fullname': 'Test User'
        }
        resp = client.simulate_post(path='/auth/registration', json=req_data)
        assert resp.status == falcon.HTTP_422
        assert resp.json['code'] == 'entity_error'
        assert 'email' in resp.json['errors']
        assert 'password1' in resp.json['errors']
        assert 'password2' in resp.json['errors']

    def test_invalid_email(self, client):
        req_data = {
            'email': 'not_valid@email',
            'password1': '123!a!b!c!',
            'password2': '123!a!b!c!',
        }
        resp = client.simulate_post(path='/auth/registration', json=req_data)
        assert resp.status == falcon.HTTP_422
        assert resp.json['code'] == 'entity_error'
        assert 'email' in resp.json['errors']

    @pytest.mark.django_db
    def test_invalid_password(self, client):
        req_data = {
            'email': 'test@mc.gov.pl',
            'password1': '123.aBc',
            'password2': '123.aBc',
        }
        resp = client.simulate_post(path='/auth/registration', json=req_data)
        assert resp.status == falcon.HTTP_422
        assert resp.json['code'] == 'entity_error'
        assert 'password1' in resp.json['errors']
        assert 'password2' not in resp.json['errors']

        req_data = {
            'email': 'test@mc.gov.pl',
            'password1': '12.34a.bCd!',
            'password2': '12.34a.bCd!!',
        }
        resp = client.simulate_post(path='/auth/registration', json=req_data)
        assert resp.status == falcon.HTTP_422
        assert resp.json['code'] == 'entity_error'
        assert 'password1' in resp.json['errors']
        assert 'password2' not in resp.json['errors']

    @pytest.mark.django_db
    def test_valid_registration(self, client):
        req_data = {
            'email': 'tester@mc.gov.pl',
            'password1': '123!A!b!c!',
            'password2': '123!A!b!c!',
        }
        resp = client.simulate_post(path='/auth/registration', json=req_data)
        assert resp.status == falcon.HTTP_200
        assert 'data' in resp.json
        assert 'id' in resp.json['data']
        assert 'attributes' in resp.json['data']
        attibutes = resp.json['data']['attributes']
        assert {'email', 'state'} <= set(attibutes)
        assert not {'password1', 'password2', 'fullname', 'phone', 'phone_internal'} <= set(attibutes)
        assert attibutes['state'] == 'pending'
        assert RegistrationSerializer().validate(resp.json) == {}

        req_data['email'] = 'tester2@mc.gov.pl'
        req_data['fullname'] = 'Test User 2'

        shutil.rmtree(settings.EMAIL_FILE_PATH, ignore_errors=True)

        resp = client.simulate_post(path='/auth/registration', json=req_data)
        assert resp.status == falcon.HTTP_200
        assert 'data' in resp.json
        assert 'id' in resp.json['data']
        assert 'attributes' in resp.json['data']
        attibutes = resp.json['data']['attributes']
        assert {'email', 'state', 'fullname'} <= set(attibutes)
        assert not {'password1', 'password2'} <= set(attibutes)
        assert attibutes['state'] == 'pending'
        assert attibutes['fullname'] == req_data['fullname']
        assert RegistrationSerializer().validate(resp.json) == {}

        assert len(os.listdir(settings.EMAIL_FILE_PATH)) == 1
        filename = os.path.join(settings.EMAIL_FILE_PATH, os.listdir(settings.EMAIL_FILE_PATH)[0])
        f = open(filename)
        assert 'To: %s' % req_data['email'] in f.read()
        f.seek(0)

        usr = User.objects.get(email=req_data['email'])
        token = usr.email_validation_token
        validation_path = settings.EMAIL_VALIDATION_PATH % token
        link = "%s%s" % (settings.BASE_URL, validation_path)
        assert link in f.read()

    @pytest.mark.django_db
    def test_registration_account_already_exist(self, client):
        req_data = {
            'email': 'tester@mc.gov.pl',
            'password1': '123!a!B!c!',
            'password2': '123!a!B!c!',
        }
        resp = client.simulate_post(path='/auth/registration', json=req_data)
        assert resp.status == falcon.HTTP_200
        resp = client.simulate_post(path='/auth/registration', json=req_data)
        assert resp.status == falcon.HTTP_403

    @pytest.mark.django_db
    def test_registration_can_change_user_state(self, client):
        req_data = {
            'email': 'tester@mc.gov.pl',
            'password1': '123!a!B!c!',
            'password2': '123!a!B!c!',
            'state': 'active'
        }
        resp = client.simulate_post(path='/auth/registration', json=req_data)
        assert resp.status == falcon.HTTP_200
        assert 'data' in resp.json
        assert 'attributes' in resp.json['data']
        attributes = resp.json['data']['attributes']
        assert attributes['state'] == 'pending'
        usr = User.objects.get(id=resp.json['data']['id'])
        assert usr.state == 'pending'

    @pytest.mark.django_db
    def test_cant_register_same_user_twice_with_diffrent_case_of_letter(self, client, editor_user):
        req_data = {
            'email': editor_user.email.upper(),
            'password1': '123!a!B!c!',
            'password2': '123!a!B!c!',
            'state': 'active'
        }
        resp = client.simulate_post(path='/auth/registration', json=req_data)
        assert resp.status == falcon.HTTP_403


class TestLogout(object):

    def test_logout_by_not_logged_in(self, client):
        resp = client.simulate_post(path='/auth/logout')
        assert resp.status == falcon.HTTP_401
        assert resp.json['code'] == 'token_missing'

    @pytest.mark.django_db
    def test_logout(self, client, active_user):
        flush_sessions()
        resp = client.simulate_post(path='/auth/login', json={
            'email': active_user.email,
            'password': 'Britenet.1'
        })

        active_usr_token = resp.json['data']['attributes']['token']
        session_valid = active_user.check_session_valid('%s %s' % (settings.JWT_HEADER_PREFIX, active_usr_token))

        assert resp.status == falcon.HTTP_200
        assert session_valid is True

        active_user2 = User.objects.create_user('test-active2@example.com', 'Britenet.1')
        active_user2.state = 'active'
        active_user2.save()

        resp = client.simulate_post(path='/auth/login', json={
            'email': active_user2.email,
            'password': 'Britenet.1'
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
    def test_get_profile_not_logged_user(self, client):
        resp = client.simulate_get(path='/auth/user')
        assert resp.status == falcon.HTTP_401
        assert resp.json['code'] == 'token_missing'

    @pytest.mark.django_db
    def test_get_profile_after_logout(self, client, active_user):
        resp = client.simulate_post(path='/auth/login', json={
            'email': active_user.email,
            'password': 'Britenet.1'
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

    @pytest.mark.django_db
    def test_get_valid_profile(self, client, active_user):
        resp = client.simulate_post(path='/auth/login', json={
            'email': active_user.email,
            'password': 'Britenet.1'
        })

        assert resp.status == falcon.HTTP_200
        token = resp.json['data']['attributes']['token']
        resp = client.simulate_get(path='/auth/user', headers={
            "Authorization": "Bearer %s" % token
        })
        assert resp.status == falcon.HTTP_200
        assert 'data' in resp.json
        assert 'id' in resp.json['data']
        assert 'attributes' in resp.json['data']
        result = resp.json['data']['attributes']
        assert {'email', 'state'} <= set(result)
        assert not {'password1', 'password2', 'fullname'} <= set(result)
        assert result['state'] == 'active'
        assert RegistrationSerializer().validate(resp.json) == {}

    @pytest.mark.django_db
    def test_profile_update(self, client, active_user, inactive_user):
        resp = client.simulate_post(path='/auth/login', json={
            'email': active_user.email,
            'password': 'Britenet.1'
        })

        assert resp.status == falcon.HTTP_200
        token = resp.json['data']['attributes']['token']
        resp = client.simulate_put(path='/auth/user', headers={
            "Authorization": "Bearer %s" % token}, json={
            "fullname": "AAAA BBBB",
        })
        assert resp.status == falcon.HTTP_200
        assert 'data' in resp.json
        assert 'attributes' in resp.json['data']
        assert resp.json['data']['attributes']['fullname'] == 'AAAA BBBB'


class TestResetPassword(object):
    @pytest.mark.django_db
    def test_sending_email(self, client, active_user):
        shutil.rmtree(settings.EMAIL_FILE_PATH, ignore_errors=True)

        resp = client.simulate_post(path='/auth/password/reset', json={
            'email': active_user.email,
        })

        assert resp.status == falcon.HTTP_200
        assert len(os.listdir(settings.EMAIL_FILE_PATH)) == 1
        filename = os.path.join(settings.EMAIL_FILE_PATH, os.listdir(settings.EMAIL_FILE_PATH)[0])
        f = open(filename)
        assert 'To: %s' % active_user.email in f.read()
        f.seek(0)
        reset_path = settings.PASSWORD_RESET_PATH % active_user.password_reset_token
        link = "%s%s" % (settings.BASE_URL, reset_path)
        assert link in f.read()

    @pytest.mark.django_db
    def test_wrong_email(self, client, active_user):
        resp = client.simulate_post(path='/auth/password/reset', json={
            'email': 'wrong_email_address',
        })

        assert resp.status == falcon.HTTP_422

        resp = client.simulate_post(path='/auth/password/reset', json={
            'email': 'this_email@doesnotex.ist',
        })

        assert resp.status == falcon.HTTP_404

    @pytest.mark.django_db
    def test_smtp_backend_error(self, client, active_user, mocker):
        mocker.patch('mcod.users.views.send_mail', side_effect=smtplib.SMTPException)
        resp = client.simulate_post(path='/auth/password/reset', json={
            'email': active_user.email,
        })

        assert resp.status == falcon.HTTP_500


class TestResetPasswordConfirm(object):
    @pytest.mark.django_db
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

    @pytest.mark.django_db
    def test_invalid_expired_token(self, client, active_user):
        url = '/auth/password/reset/abcdedfg'

        data = {
            'new_password1': '123.4.bcE',
            'new_password2': '123.4.bcE'
        }

        resp = client.simulate_post(url, json=data)
        assert resp.status == falcon.HTTP_404

        url = '/auth/password/reset/8c37fd0c-5600-4277-a13a-67ced4a61e66'

        data = {
            'new_password1': '123.4.bcE',
            'new_password2': '123.4.bcE'
        }

        resp = client.simulate_post(url, json=data)
        assert resp.status == falcon.HTTP_404

        token = active_user.password_reset_token

        token_obj = active_user.tokens.filter(token=token).first()

        assert token_obj.is_valid is True

        token_obj.invalidate()

        assert token_obj.is_valid is False

        url = '/auth/password/reset/%s' % token

        resp = client.simulate_post(url, json=data)
        assert resp.status == falcon.HTTP_400
        assert resp.json['code'] == 'expired_token'


class TestChangePassword(object):
    @pytest.mark.django_db
    def test_password_change_errors(self, client, active_user):
        resp = client.simulate_post(path='/auth/login', json={
            'email': active_user.email,
            'password': 'Britenet.1'
        })

        assert resp.status == falcon.HTTP_200
        assert 'data' in resp.json
        assert 'attributes' in resp.json['data']
        token = resp.json['data']['attributes']['token']

        resp = client.simulate_post(path='/auth/password/change',
                                    headers={
                                        "Authorization": "Bearer %s" % token
                                    },
                                    json={
                                        "old_password": "AAAA.BBBB12",
                                        "new_password1": "AaCc.5922",
                                        "new_password2": "AaCc.5922",
                                    })

        assert resp.status == falcon.HTTP_422
        assert resp.json['code'] == 'entity_error'

        resp = client.simulate_post(path='/auth/password/change',
                                    headers={
                                        "Authorization": "Bearer %s" % token
                                    },
                                    json={
                                        "old_password": "Britenet.1",
                                        "new_password1": "AaCc.5922",
                                        "new_password2": "AaCc.59222",
                                    })

        assert resp.status == falcon.HTTP_422
        assert resp.json['code'] == 'entity_error'

        resp = client.simulate_post(path='/auth/password/change',
                                    headers={
                                        "Authorization": "Bearer %s" % token
                                    },
                                    json={
                                        "old_password": "Britenet.1",
                                        "new_password1": "Abcde",
                                        "new_password2": "Abcde",
                                    })

        assert resp.status == falcon.HTTP_422
        assert resp.json['code'] == 'entity_error'

    @pytest.mark.django_db
    def test_password_change(self, client, active_user):
        resp = client.simulate_post(path='/auth/login', json={
            'email': active_user.email,
            'password': 'Britenet.1'
        })

        assert resp.status == falcon.HTTP_200
        token = resp.json['data']['attributes']['token']

        data = {
            "old_password": "Britenet.1",
            "new_password1": "AaCc.5922",
            "new_password2": "AaCc.5922",
        }
        resp = client.simulate_post(path='/auth/password/change',
                                    headers={
                                        "Authorization": "Bearer %s" % token
                                    },
                                    json=data)

        assert resp.status == falcon.HTTP_200

        usr = User.objects.get(pk=active_user.id)
        assert usr.check_password(data['new_password1']) is True


class TestResendActivationMail(object):
    @pytest.mark.django_db
    def test_resending(self, client, inactive_user):
        shutil.rmtree(settings.EMAIL_FILE_PATH, ignore_errors=True)
        resp = client.simulate_post(path='/auth/registration/resend-email',
                                    json={
                                        'email': inactive_user.email
                                    }
                                    )
        assert resp.status == falcon.HTTP_200
        assert {} == resp.json

        assert len(os.listdir(settings.EMAIL_FILE_PATH)) == 1
        filename = os.path.join(settings.EMAIL_FILE_PATH, os.listdir(settings.EMAIL_FILE_PATH)[0])
        f = open(filename)
        assert 'To: %s' % inactive_user.email in f.read()
        f.seek(0)

        usr = User.objects.get(email=inactive_user.email)
        token = usr.email_validation_token
        validation_path = settings.EMAIL_VALIDATION_PATH % token
        link = "%s%s" % (settings.BASE_URL, validation_path)
        assert link in f.read()

    @pytest.mark.django_db
    def test_wrong_email(self, client):
        data = {
            'email': 'this_is_so_wrong'
        }

        resp = client.simulate_post(path='/auth/registration/resend-email', json=data)
        assert resp.status == falcon.HTTP_422
        assert 'email' in resp.json['errors']

        data = {
            'email': 'not_existing_email@example.com'
        }

        resp = client.simulate_post(path='/auth/registration/resend-email', json=data)
        assert resp.status == falcon.HTTP_404

    @pytest.mark.django_db
    def test_smtp_backend_error(self, active_user, client, mocker):
        mocker.patch('mcod.users.views.send_mail', side_effect=smtplib.SMTPException)
        resp = client.simulate_post(path='/auth/registration/resend-email', json={
            'email': active_user.email,
        })

        assert resp.status == falcon.HTTP_500


class TestVerifyEmail(object):
    @pytest.mark.django_db
    def test_pending_user(self, client, inactive_user):
        token = inactive_user.email_validation_token
        resp = client.simulate_get(path='/auth/registration/verify-email/%s/' % token)
        assert resp.status == falcon.HTTP_200

        usr = User.objects.get(email=inactive_user)
        assert usr.state == 'active'
        token_obj = usr.tokens.filter(token=token).first()
        assert token_obj.is_valid is False
        assert usr.email_confirmed.date() == timezone.now().date()

    @pytest.mark.django_db
    def test_blocked_user(self, client, blocked_user):
        token = blocked_user.email_validation_token
        resp = client.simulate_get(path='/auth/registration/verify-email/%s/' % token)
        assert resp.status == falcon.HTTP_200

        usr = User.objects.get(email=blocked_user)
        assert usr.state == 'blocked'
        token_obj = usr.tokens.filter(token=token).first()
        assert token_obj.is_valid is False
        assert usr.email_confirmed.date() == timezone.now().date()

    @pytest.mark.django_db
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
    @pytest.mark.django_db
    def test_extended_permissions(self, active_user):
        header = get_auth_header(
            active_user.email,
            active_user.system_role,
            '1'
        )

        payload = decode_jwt_token(header)
        assert payload['user']['role'] == 'user'

        active_user.is_staff = True

        header = get_auth_header(
            active_user.email,
            active_user.system_role,
            '1'
        )

        payload = decode_jwt_token(header)
        assert payload['user']['role'] == 'staff'

        active_user.is_staff = False
        active_user.is_superuser = True

        header = get_auth_header(
            active_user.email,
            active_user.system_role,
            '1'
        )

        payload = decode_jwt_token(header)
        assert payload['user']['role'] == 'staff'


@pytest.mark.django_db
def test_users_autocomplete_view(admin_user):
    client = Client()
    client.force_login(admin_user)

    response = client.get(reverse("user-autocomplete"))

    assert len(response.json()['results']) == 1
    assert response.json()['results'][0]['id'] == str(admin_user.id)
    assert response.json()['results'][0]['text'] == admin_user.email


@pytest.mark.django_db
def test_admin_autocomplete_view_for_superuser(admin_user, editor_user):
    client = Client()
    client.force_login(admin_user)

    response = client.get(reverse("admin-autocomplete"))

    assert len(response.json()['results']) == 1
    assert response.json()['results'][0]['id'] == str(admin_user.id)
    assert response.json()['results'][0]['text'] == admin_user.email


@pytest.mark.django_db
def test_admin_autocomplete_view_for_not_superuser(admin_user, editor_user):
    client = Client()
    client.force_login(editor_user)

    response = client.get(reverse("admin-autocomplete"))

    assert len(response.json()['results']) == 0
