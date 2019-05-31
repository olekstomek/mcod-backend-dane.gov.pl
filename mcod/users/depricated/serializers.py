import marshmallow as ma
import marshmallow_jsonapi as ja
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from mcod.lib.serializers import BasicSerializer


class UserSchema(ja.Schema):
    id = ma.fields.Int(required=True, faker_type='int', example=77)
    state = ma.fields.Str(required=True,
                          faker_type='userstate', example='active',
                          description="Allowed values: 'active', 'inactive' or 'blocked'")
    email = ma.fields.Email(required=True,
                            faker_type='email', example='user@example.com')
    fullname = ma.fields.Str(missing=None,
                             faker_type='name', example='Jan Kowalski')
    about = ma.fields.Str(missing=None, faker_type='sentence',
                          example='I am a very talented programmer.')
    created = ma.fields.Date()
    count_datasets_created = ma.fields.Int()
    count_datasets_modified = ma.fields.Int()

    @ma.validates('state')
    def check_state(self, value):
        if value not in settings.USER_STATE_LIST:
            raise ValidationError(_('Invalid user state.'))


class UserSerializer(UserSchema, BasicSerializer):
    class Meta:
        type_ = 'user'
        strict = True
        self_url = '/auth/user'


class LoginSchema(UserSchema):
    token = ma.fields.Str(required=True, faker_type='uuid4',
                          example='bieth8Shoonu1che4laegahw2ue!ch3iem5ahx7oonohng3le5mooquohp4ooWa')


class LoginSerializer(LoginSchema, BasicSerializer):
    class Meta:
        type_ = 'user'
        strict = True
        self_url = '/auth/user'


class RegistrationSerializer(UserSchema, BasicSerializer):
    class Meta:
        type_ = 'user'
        strict = True
        self_url = '/'
