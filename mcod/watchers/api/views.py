# -*- coding: utf-8 -*-

from functools import partial

import falcon
from django.apps import apps
from django.core.paginator import Paginator

from mcod.core.api.handlers import RetrieveOneHdlr, RetrieveManyHdlr, CreateOneHdlr, UpdateOneHdlr, RemoveOneHdlr
from mcod.core.api.hooks import login_required
from mcod.core.api.views import BaseView
from mcod.watchers.api import deserializers as d
from mcod.watchers.api.schemas.response import SubscriptionResponse, NotificationResponse


class SubscriptionsView(BaseView):
    @falcon.before(login_required)
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_required)
    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST, *args, **kwargs)

    class POST(CreateOneHdlr):
        deserializer_schema = d.CreateSubscription()
        serializer_schema = SubscriptionResponse(many=False)
        database_model = apps.get_model('watchers', 'Subscription')

        def _data(self, request, *args, **kwargs):
            Subscription = self.database_model
            instance = Subscription.objects.create_from_request(request)
            return instance

    class GET(RetrieveManyHdlr):
        deserializer_schema = partial(d.FetchSubscriptions)
        serializer_schema = partial(SubscriptionResponse, many=True)
        database_model = apps.get_model('watchers', 'Subscription')

        def clean(self, *args, validators=None, locations=None, **kwargs):
            result = super().clean(*args, validators == validators, locations=locations, **kwargs)
            return result

        def _get_queryset(self, *args, **kwargs):
            cleaned = self.request.context.cleaned_data
            qs = self.database_model.objects.all()
            page, per_page = cleaned.pop('page', 1), cleaned.pop('per_page', 20)
            if cleaned:
                qs = qs.filter(**cleaned)

            paginator = Paginator(qs, per_page)
            result = paginator.get_page(page)
            return result


class SubscriptionView(BaseView):
    @falcon.before(login_required)
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    @falcon.before(login_required)
    def on_patch(self, request, response, *args, **kwargs):
        self.handle(request, response, self.PATCH, *args, **kwargs)

    @falcon.before(login_required)
    def on_delete(self, request, response, *args, **kwargs):
        self.handle(request, response, self.DELETE, *args, **kwargs)

    class PATCH(UpdateOneHdlr):
        deserializer_schema = d.UpdateSubscription()
        serializer_schema = SubscriptionResponse(many=False)
        database_model = apps.get_model('watchers', 'Subscription')

        def _data(self, request, id, *args, **kwargs):
            data = request.cleaned['data']['attributes']
            try:
                instance = self.database_model.objects.get(pk=id)
            except self.database_model.DoesNotExist:
                raise falcon.HTTPNotFound

            self.database_model.objects.filter(id=id).update(**data)

            instance.refresh_from_db()
            return instance

    class DELETE(RemoveOneHdlr):
        database_model = apps.get_model('watchers', 'Subscription')

    class GET(RetrieveOneHdlr):
        deserializer_schema = d.FetchSubscription()
        serializer_schema = SubscriptionResponse(many=False)
        database_model = apps.get_model('watchers', 'Subscription')

        def _clean(self, request, id, *args, **kwargs):
            model = self.database_model
            try:
                return model.objects.get(pk=id, user=request.user)
            except model.DoesNotExist:
                raise falcon.HTTPNotFound


class NotificationsView(BaseView):
    @falcon.before(login_required)
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(RetrieveManyHdlr):
        deserializer_schema = d.FetchNotifications()
        serializer_schema = NotificationResponse(many=True)
        database_model = apps.get_model('watchers', 'Notification')

        def _clean(self, request, *args, locations=None, **kwargs):
            result = super()._clean(request, *args, locations=locations, **kwargs)
            result['subscription__user_id'] = request.user.id
            return result

        def _get_queryset(self, params, id=None, **kwargs):
            qs = self.database_model.objects.all()
            page, per_page = params.pop('page', 1), params.pop('per_page', 20)
            if params:
                qs = qs.filter(**params)
            if id:
                qs = qs.filter(subscription_id=id)
            paginator = Paginator(qs, per_page)
            result = paginator.get_page(page)
            return result


class NotificationView(BaseView):
    @falcon.before(login_required)
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(RetrieveOneHdlr):
        deserializer_schema = d.FetchNotification()
        serializer_schema = NotificationResponse(many=False)
        database_model = apps.get_model('watchers', 'Notification')

        def _clean(self, request, id, *args, **kwargs):
            model = self.database_model
            try:
                return model.objects.get(pk=id, subscription__user_id=request.user.id)
            except model.DoesNotExist:
                raise falcon.HTTPNotFound
