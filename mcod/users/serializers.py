from django.utils.translation import gettext_lazy as _

from mcod.core.api import fields
from mcod.core.serializers import CSVSerializer


class UserCSVSerializer(CSVSerializer):
    id = fields.Int(data_key=_('ID'), required=True, example=77)
    email = fields.Email(data_key=_('Email'), default='', required=True, example='user@example.com')
    fullname = fields.Str(data_key=_('Full name'), default='', example='Jan Kowalski')
    official_phone = fields.Method('get_phone', data_key=_('Official phone'), example='+481234567890')
    role = fields.Method('get_role', data_key=_('Role'), default='', example='+481234567890')
    state = fields.Str(data_key=_('State'), required=True, example='active',
                       description="Allowed values: 'active', 'inactive' or 'blocked'")
    institution = fields.Method('get_institutions', data_key=_('Institution'), example='Ministerstwo Cyfryzacji')

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
