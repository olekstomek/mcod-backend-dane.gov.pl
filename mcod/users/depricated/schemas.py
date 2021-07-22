# -*- coding: utf-8 -*-
import falcon
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as dj_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.utils.translation import gettext as _
from marshmallow import Schema, ValidationError, validates_schema, post_load

from mcod.lib import fields

# from mcod.lib.decorators import validate_request, session_store, login_required

# from mcod.lib.resources.resources import BaseResourceOld

User = get_user_model()


class AccountUpdate(Schema):
    """
        Update user profile (for authenticated user, a.k.a. show my profile)
    """
    fullname = fields.Str()
    phone = fields.Str()
    subscriptions_report_opt_in = fields.Boolean()
    rodo_privacy_policy_opt_in = fields.Boolean()

    # about = fields.Str(
    #   missing=None, faker_type='sentence', example='I am a very talented programmer.')

    class Meta:
        strict = True

    @post_load
    def prepare_data(self, data, **kwargs):
        se = data.get('subscriptions_report_opt_in', None)
        pp = data.get('rodo_privacy_policy_opt_in', None)
        now = timezone.now()
        if se is not None:
            data['subscriptions_report_opt_in'] = now if se else None
        if pp is not None:
            data['rodo_privacy_policy_opt_in'] = now if pp else None
        return data


class Registration(AccountUpdate):
    """
        User registration
    """
    email = fields.Email(required=True,
                         faker_type='email', example='user@example.com')
    password1 = fields.Str(required=True, faker_type='password', example='Kai7!!phoom')
    password2 = fields.Str(required=True, faker_type='password', example='Kai7!!phoom')

    @validates_schema()
    def validate_passwords(self, data, **kwargs):
        if 'password1' in data:
            try:
                dj_validate_password(data['password1'])
            except DjangoValidationError as e:
                raise ValidationError(e.error_list[0].message, field_name='password1', code=e.error_list[0].code,
                                      field_names=['password1', ])
            if 'password2' in data:
                if data['password1'] != data['password2']:
                    raise ValidationError(_('Passwords not match'), field_name='password1',
                                          field_names=['password1', 'password2'])

    @post_load
    def prepare_data(self, data, **kwargs):
        data['password'] = data['password1']
        data.pop('password1')
        data.pop('password2')
        data.pop('subscriptions_report_opt_in', None)
        return data

    def clean(self, request, locations=None):
        cleaned = super().clean(request, locations=locations)
        usr = User.objects.get_or_none(email=cleaned['email'].strip())
        if usr:
            raise falcon.HTTPForbidden(
                description=_('Account for this email already exist')
            )

        # Model validation
        usr = User(**cleaned)
        self.clean_model(usr)
        return cleaned

    class Meta:
        strict = True


class PasswordChange(Schema):
    """
        Password change - for logged user (change my password)
    """
    old_password = fields.Str(required=True, faker_type='password', description='Current password',
                              example='Kai7!!phoom')
    new_password1 = fields.Str(required=True, faker_type='password', description='New password', example='Msww8.1dF')
    new_password2 = fields.Str(required=True, faker_type='password', description='New password (repeat)',
                               example='Msww8.1dF')

    class Meta:
        strict = True


class PasswordReset(Schema):
    """
        Password reset - flow start (reset my password)
    """
    email = fields.Email(required=True,
                         faker_type='email', example='user@example.com')

    class Meta:
        strict = True


class PasswordResetConfirm(Schema):
    """
        Password reset - flow end (set new password)
    """
    # auth_token = fields.Str(required=True, faker_type='uuid', description='Password reset auth token',
    #                        example='8c37fd0c-5600-4277-a13a-67ced4a61e66')
    new_password1 = fields.Str(required=True, faker_type='password', description='New password', example='Msww8.1dF')
    new_password2 = fields.Str(required=True, faker_type='password', description='New password (repeat)',
                               example='Msww8.1dF')

    @validates_schema()
    def validate_passwords(self, data, **kwargs):
        if 'new_password1' in data:
            try:
                dj_validate_password(data['new_password1'])
            except DjangoValidationError as e:
                raise ValidationError(e.error_list[0].message, field_name='new_password1', code=e.error_list[0].code)
            #     raise ValidationError(e.error_list[0].message, code=e.error_list[0].code,
            #                           field_names=['new_password1', ])
            if 'new_password2' in data:
                if data['new_password1'] != data['new_password2']:
                    raise ValidationError(_('Passwords not match'), field_name='new_password1',
                                          field_names=['new_password1', 'new_password2'])

    class Meta:
        strict = True


# class EmailConfirmRequest(Schema):
#     token = fields.Str(required=True, error_messages=str_error_messages, faker_type='uuid4',
#                        example='bieth8Shoonu1che4laegahw2ue!ch3iem5ahx7oonohng3le5mooquohp4ooWa')
#
#     class Meta:
#         strict = True


class ResendActivationEmail(Schema):
    """
        Password reset - flow start (reset my password)
    """
    email = fields.Email(required=True,
                         faker_type='email', example='user@example.com')

    class Meta:
        strict = True
