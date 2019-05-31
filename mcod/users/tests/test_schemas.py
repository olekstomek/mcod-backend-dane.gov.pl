import pytest
from django.contrib.auth import get_user_model

from mcod.users.depricated.schemas import Login, Registration  # , RegistrationRequest

User = get_user_model()


@pytest.fixture()
def db_user():
    usr = User(
        email='test@example.com',
        password='S3cr3tPass',
        state='active'
    )
    usr.save()
    return usr


@pytest.fixture()
def user_dict():
    return {
        'email': 'test@example.com',
        'password': 'S3cr3tPass1'
    }


class Common(object):
    def _test_serialized_user(self, user, schema):
        d = schema().dump(user)
        result = schema().validate(d)
        assert result == {}

    def _test_email(self, user_dict, schema):
        for wrong_email in ['abc', 'abc@', '@abc', 'abc@abc', '']:
            user_dict['email'] = wrong_email
            res = schema().validate(user_dict)
            assert 'email' in res

        user_dict.pop('email')
        res = schema().validate(user_dict)
        assert 'email' in res


# class TestAccountSchema(Common):
#     @pytest.mark.django_db
#     def test_serialization_from_model(self, db_user):
#         self._test_serialized_user(db_user, AccountSchema)
#
#     def test_wrong_or_missing_email(self, user_dict):
#         self._test_email(user_dict, AccountSchema)
#
#     def test_wrong_or_missing_state(self, user_dict):
#         for wrong_state in ['abc', '', 1]:
#             user_dict['state'] = wrong_state
#             with pytest.raises(marshmallow.exceptions.ValidationError) as e:
#                 AccountSchema().validate(user_dict)
#             assert 'state' in e.value.messages
#
#         user_dict.pop('state')
#         with pytest.raises(marshmallow.exceptions.ValidationError) as e:
#             AccountSchema().validate(user_dict)
#         assert 'state' in e.value.messages


class TestLogin(Common):
    @pytest.mark.django_db
    def test_serialization_from_model(self, db_user):
        db_user.token = 'abcdef'
        self._test_serialized_user(db_user, Login)

    def test_missing_password(self, user_dict):
        result = Login().validate({'email': 'test@example.com'})
        assert 'password' in result

    def test_missing_email(self, user_dict):
        res = Login().validate({'password': '123'})
        assert 'email' in res


class TestRegistrationRequest():
    def test_invalid_password(self, invalid_passwords):
        for password in invalid_passwords:
            data = {
                'email': 'test@mc.gov.pl',
                'password1': password,
                'password2': password
            }
            res = Registration().validate(data)
            assert 'password1' in res

    def test_password_not_match(self):
        data = {
            'email': 'admin@mc.gov.pl',
            'password1': 'e3!dEpc@7!',
            'password2': 'e3!dEpc@7'
        }
        res = Registration().validate(data)

        assert 'password1' in res
        assert 'password2' not in res

    def test_field_missing(self):
        data = {
            'email': 'admin@mc.gov.pl',
            'password1': 'e3!dEpc@7!',
        }
        res = Registration().validate(data)
        assert 'password2' in res

        data = {
            'email': 'admin@mc.gov.pl',
            'password2': 'e3!dEpc@7!',
        }
        res = Registration().validate(data)
        assert 'password1' in res

        data = {
            'password1': 'e3!dEpc@7!',
            'password2': 'e3!dEpc@7!',
        }
        res = Registration().validate(data)
        assert 'email' in res

    def test_invalid_email(self):
        data = {
            'email': 'notanemailaddress@',
            'password1': 'e3!dEpc@7!',
            'password2': 'e3!dEpc@7!'
        }
        res = Registration().validate(data)
        assert 'email' in res

    def test_valid_data(self):
        data = {
            'email': 'admin@mc.gov.pl',
            'password1': 'e3!dEpc@7!',
            'password2': 'e3!dEpc@7!'
        }
        result = Registration().validate(data)
        assert result == {}
