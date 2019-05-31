from django.utils.translation import gettext as _
from marshmallow import validate

from mcod.core.api.schemas import ListingSchema, CommonSchema
from mcod.core.api.search import fields
from mcod.watchers.models import NOTIFICATION_TYPES, NOTIFICATION_STATUS_CHOICES

ALLOWED_NOTIFICATION_TYPES = [i[0] for i in NOTIFICATION_TYPES]
ALLOWED_STATUS_CHOICES = [i[0] for i in NOTIFICATION_STATUS_CHOICES]


class SubscriptionsRequest(ListingSchema):
    watcher__object_name__endswith = fields.StringField(data_key='object_name', description='Object name',
                                                        example='resource', required=False)
    watcher__object_ident = fields.StringField(data_key='object_id', description='Object ID', example='3776',
                                               required=False)

    class Meta:
        strict = True
        ordered = True


class SubscriptionRequest(CommonSchema):
    id = fields.NumberField(
        _in='path', description='Subscription ID', example='447', required=True
    )

    class Meta:
        strict = True
        ordered = True


class NotificationsRequest(ListingSchema):
    subscription__watcher__object_name__endswith = fields.StringField(data_key='object_name',
                                                                      description='Object name',
                                                                      example='resource', required=False)
    subscription__watcher__object_ident = fields.StringField(data_key='object_id', description='Object ID',
                                                             example='3776',
                                                             required=False)
    notification_type = fields.StringField(description='Type of notificaton', example='object_updated',
                                           required=False,
                                           validate=validate.OneOf(choices=ALLOWED_NOTIFICATION_TYPES,
                                                                   error=_('Invalid notification type')))
    status = fields.StringField(description='Message status (new or read)', example='new', required=False,
                                validate=validate.OneOf(choices=ALLOWED_STATUS_CHOICES,
                                                        error=_('Invalid notification status')))

    class Meta:
        strict = True
        ordered = True


class NotificationRequest(CommonSchema):
    id = fields.NumberField(
        _in='path', description='Notification ID', example='447', required=True
    )

    class Meta:
        strict = True
        ordered = True
