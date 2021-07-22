import marshmallow as ma
import marshmallow_jsonapi as ja
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from mcod.core.api import fields as api_fields
from mcod.core.serializers import CSVSerializer
from mcod.lib.serializers import BasicSchema, TranslatedStr


class UserCSVSerializer(CSVSerializer):
    id = api_fields.Int(data_key=_('id'), required=True, example=77)
    email = api_fields.Email(data_key=_('Email'), default='', required=True, example='user@example.com')
    fullname = api_fields.Str(data_key=_('Full name'), default='', example='Jan Kowalski')
    official_phone = api_fields.Method('get_phone', data_key=_('Official phone'), example='+481234567890')
    role = api_fields.Method('get_role', data_key=_('Role'), default='', example='+481234567890')
    state = api_fields.Str(data_key=_('State'), required=True, example='active',
                           description="Allowed values: 'active', 'inactive' or 'blocked'")
    institution = api_fields.Method('get_institutions', data_key=_('Institution'), example='Ministerstwo Cyfryzacji')

    def get_phone(self, obj):
        if obj.phone:
            phone = obj.phone
            if obj.phone_internal:
                phone += f'.{obj.phone_internal}'
            return phone
        return ''

    def get_role(self, obj):
        if obj.is_superuser:
            return _('Admin')
        elif obj.is_staff:
            return _('Editor')
        else:
            return _('User')

    def get_institutions(self, obj):
        return ','.join(str(org.id) for org in obj.organizations.all())

    class Meta:
        ordered = True
        model = 'users.User'


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
    subscriptions_report_opt_in = ma.fields.Boolean()
    rodo_privacy_policy_opt_in = ma.fields.Boolean()
    count_datasets_created = ma.fields.Int()
    count_datasets_modified = ma.fields.Int()

    @ma.validates('state')
    def check_state(self, value):
        if value not in settings.USER_STATE_LIST:
            raise ValidationError(_('Invalid user state.'))

    @ma.post_dump
    def prepare_data(self, data, **kwargs):
        data['subscriptions_report_opt_in'] = True if data.get('subscriptions_report_opt_in') is not None else False
        data['rodo_privacy_policy_opt_in'] = True if data.get('rodo_privacy_policy_opt_in') is not None else False

        return data


class UserInstitution(BasicSchema):
    id = ma.fields.Int()
    title = TranslatedStr()
    slug = TranslatedStr()

    class Meta:
        type_ = 'institution'
        strict = True
        self_url = '/institutions/{institution_id}'
        self_url_kwargs = {"institution_id": "<id>",
                           "institution_slug": "<slug>"}
