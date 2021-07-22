# from marshmallow import pre_dump
#
# from mcod.core.api import fields
# from mcod.core.api import schemas
# from mcod.core.api.jsonapi import schemas as jss
#
#
# class SubscriptionAttrs(schemas.ExtSchema):
#     created = fields.DateTime()
#     modified = fields.DateTime()
#     name = fields.Str(attribute='display_name')
#     object_name = fields.Str(attribute='watcher.object_name')
#     object_url = fields.Method('get_object_url')
#     customfields = fields.Dict()
#
#     def get_object_url(self, obj):
#         if obj.watcher.watcher_type == 'model':
#             instance = obj.watcher.obj
#             return instance.api_url
#         return ''
#
#     # def get_object_type(self, obj):
#     #     if obj.watcher.watcher_type == 'model':
#     #         _, model_name = obj.watcher.object_name.split('.')
#     #         return model_name.lower()
#     #     return obj.watcher.watcher_type
#
#
# class SubscriptionObject(jss.ResponseData):
#     relationships = fields.Dict()
#
#     class Meta:
#         attr_short_cls = SubscriptionAttrs
#         attr_cls = SubscriptionAttrs
#         _type = 'subscription'
#         _path = 'auth/subscriptions'
#
#     @pre_dump(pass_many=False)
#     def prepare_relationships(self, data):
#         watcher = data.watcher
#         if watcher.watcher_type == 'model':
#             _, obj_name = watcher.object_name.split('.')
#         else:
#             obj_name = 'query'
#         obj_name = obj_name.lower()
#         setattr(data, 'relationships', {
#             'notifications': {
#                 'links': {
#                     'related': '{}/auth/subscriptions/{}/notifications'.format(self.api_url, data.id)
#                 },
#                 'meta': {
#                     'count': data.notifications.count()
#                 },
#             },
#             'subscribed_object': {
#                 'data': {
#                     'id': str(watcher.object_ident),
#                     'type': obj_name
#                 },
#                 'links': {
#                     'related': watcher.obj.api_url
#                 },
#             }
#         })
#         return data
#
#
# class SubscriptionIncludes(jss.BaseData):
#     attributes = fields.Raw()
#
#
# class SubscriptionResponse(jss.ResponseSchema):
#     included = fields.Nested(SubscriptionIncludes, many=True)
#
#     class Meta:
#         data_cls = SubscriptionObject
#         meta_cls = jss.ResponseMeta
#
#     @pre_dump(pass_many=True)
#     def prepare_included(self, request, many):
#         included = {}
#         subscriptions = request.data if many else [request.data, ]
#         for subscription in subscriptions:
#             subscribed_object = subscription.watcher.obj.serialized
#             if subscribed_object:
#                 key = '{}-{}'.format(subscribed_object['type'], subscribed_object['id'])
#                 included.setdefault(key, subscribed_object)
#
#         if included:
#             request.included = included.values()
#         return request
#
#
# class NotificationAttrs(schemas.ExtSchema):
#     _type = fields.Str(data_key='type', attribute='type')
#     status = fields.Str()
#     notification_type = fields.Str()
#     created = fields.DateTime()
#
#
# class NotificationObject(jss.ResponseData):
#     relationships = fields.Dict()
#
#     class Meta:
#         attr_short_cls = NotificationAttrs
#         attr_cls = NotificationAttrs
#         _type = 'notification'
#         _path = 'auth/notifications'
#
#     @pre_dump(pass_many=False)
#     def prepare_relationships(self, data):
#         watcher = data.subscription.watcher
#         if watcher.watcher_type == 'model':
#             _, obj_name = watcher.object_name.split('.')
#         else:
#             obj_name = 'query'
#         obj_name = obj_name.lower()
#
#         setattr(data, 'relationships', {
#             'subscription': {
#                 'data': {
#                     'id': str(data.subscription_id),
#                     'type': 'subscription'
#                 },
#                 'links': {
#                     'related': data.subscription.api_url
#                 }
#             },
#             'subscribed_object': {
#                 'data': {
#                     'id': str(watcher.object_ident),
#                     'type': obj_name
#                 },
#                 'links': {
#                     'related': watcher.obj.api_url
#                 },
#             }
#         })
#
#         return data
#
#
# class NotificationIncludes(jss.BaseData):
#     attributes = fields.Raw()
#
#
# class NotificationResponse(jss.ResponseSchema):
#     included = fields.Nested(NotificationIncludes, many=True)
#
#     class Meta:
#         data_cls = NotificationObject
#         meta_cls = jss.ResponseMeta
#
#     @pre_dump(pass_many=True)
#     def prepare_included(self, request, many):
#         included = {}
#         notifications = request.data if many else [request.data, ]
#         for notification in notifications:
#             subscribed_object = notification.subscription.watcher.obj.serialized
#             if subscribed_object:
#                 key = '{}-{}'.format(subscribed_object['type'], subscribed_object['id'])
#                 included.setdefault(key, subscribed_object)
#             key = 'subscription-{}'.format(notification.subscription_id)
#             included.setdefault(key, SubscriptionObject().dump(notification.subscription))
#
#         if included:
#             request.included = included.values()
#         return request
