from django.utils.translation import gettext as _
from marshmallow import validate, pre_load

from mcod.core.api import fields as core_fields
from mcod.core.api import schemas as core_schemas
from mcod.core.api.jsonapi import schemas as jsonapi_schemas
from mcod.core.api.search import fields as search_fields
from mcod.watchers.models import NOTIFICATION_TYPES, NOTIFICATION_STATUS_CHOICES, OBJECT_NAME_TO_MODEL

ALLOWED_NOTIFICATION_TYPES = [i[0] for i in NOTIFICATION_TYPES]
ALLOWED_STATUS_CHOICES = [i[0] for i in NOTIFICATION_STATUS_CHOICES]

ALLOWED_OBJECT_NAMES = list(OBJECT_NAME_TO_MODEL.keys()) + ['query', ]


class FetchSubscriptions(core_schemas.ListingSchema):
    watcher__object_name__endswith = search_fields.StringField(data_key='object_name', description='Object name',
                                                               example='resource', required=False)
    watcher__object_ident = search_fields.StringField(data_key='object_id', description='Object ID',
                                                      example='3776',
                                                      required=False)

    class Meta:
        strict = True
        ordered = True


class UpdateSubscriptionAttrs(core_schemas.ExtSchema):
    name = core_fields.String(description='Subscription name', example='my query 1', required=False)
    enable_notifications = core_fields.Boolean(description='Enable notifications', example=True, required=False)
    customfields = core_fields.Raw()

    class Meta:
        strict = True
        ordered = True


class CreateSubscriptionAttrs(core_schemas.ExtSchema):
    object_name = core_fields.String(description='Object name', example='resource', required=True,
                                     validate=validate.OneOf(choices=ALLOWED_OBJECT_NAMES,
                                                             error=_('Unsupported object name')))
    object_ident = core_fields.String(description='Object ID or query url.', example='12342',
                                      required=True)
    name = core_fields.String(description='Subscription name', example='my query 1', required=False)
    enable_notifications = core_fields.Boolean(description='Enable notifications', example=True, required=False)
    customfields = core_fields.Raw()

    class Meta:
        strict = True
        ordered = True

    @pre_load(pass_many=False)
    def ident_to_string(self, data):
        data['object_ident'] = str(data['object_ident'])
        return data


class CreateSubscription(jsonapi_schemas.POSTSchema):
    class Meta:
        attrs_cls = CreateSubscriptionAttrs
        _type = 'subscription'
        strict = True
        ordered = True


class UpdateSubscription(jsonapi_schemas.PATCHSchema):
    class Meta:
        attrs_cls = UpdateSubscriptionAttrs
        _type = 'subscription'
        strict = True
        ordered = True


class FetchSubscription(core_schemas.CommonSchema):
    id = search_fields.NumberField(
        _in='path', description='Subscription ID', example='447', required=True
    )

    class Meta:
        strict = True
        ordered = True


class FetchNotifications(core_schemas.ListingSchema):
    subscription__watcher__object_name__endswith = search_fields.StringField(data_key='object_name',
                                                                             description='Object name',
                                                                             example='resource', required=False)
    subscription__watcher__object_ident = search_fields.StringField(data_key='object_id', description='Object ID',
                                                                    example='3776',
                                                                    required=False)
    notification_type = search_fields.StringField(description='Type of notificaton', example='object_updated',
                                                  required=False,
                                                  validate=validate.OneOf(choices=ALLOWED_NOTIFICATION_TYPES,
                                                                          error=_('Invalid notification type')))
    status = search_fields.StringField(description='Message status (new or read)', example='new', required=False,
                                       validate=validate.OneOf(choices=ALLOWED_STATUS_CHOICES,
                                                               error=_('Invalid notification status')))

    class Meta:
        strict = True
        ordered = True


class FetchNotification(core_schemas.CommonSchema):
    id = search_fields.NumberField(
        _in='path', description='Notification ID', example='447', required=True
    )

    class Meta:
        strict = True
        ordered = True
