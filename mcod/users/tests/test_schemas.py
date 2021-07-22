import pytest
from django.contrib.auth import get_user_model


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
#
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
