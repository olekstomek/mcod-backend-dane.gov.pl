# -*- coding: utf-8 -*-
import json

import falcon
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from elasticsearch_dsl.document import Document

from mcod.lib.encoders import DateTimeToISOEncoder


class ApiViewMeta(type):
    def __new__(mcs, name, bases, namespace, **kwargs):  # noqa:C901
        cls = super().__new__(mcs, name, bases, namespace)

        if 'Meta' not in namespace:
            cls.Meta = type('Meta', (type,), {'abstract': False})

        if not hasattr(cls.Meta, 'abstract'):
            cls.Meta.abstract = False

        if not cls.Meta.abstract:
            cls.allowed_methods = [
                method for method, allowed in (
                    ('GET', hasattr(cls, 'on_get')),
                    ('POST', hasattr(cls, 'on_post')),
                    ('PUT', hasattr(cls, 'on_put')),
                    ('PATCH', hasattr(cls, 'on_patch')),
                    ('DELETE', hasattr(cls, 'on_delete')),
                    ('HEAD', hasattr(cls, 'on_head')),
                    ('OPTIONS', hasattr(cls, 'on_options')),
                ) if allowed
            ]
            for method in cls.allowed_methods:
                if method not in namespace:
                    setattr(cls, method, type(method, (object,), {}))
                method_cls = getattr(cls, method)

                # Apply triggers (a.k.a falcon's hooks)
                if hasattr(method_cls, 'triggers'):
                    func_name = 'on_' + method.lower()
                    func = getattr(cls, func_name)
                    for trigger in method_cls.triggers:
                        func = trigger.wrap(func)
                    setattr(cls, func_name, func)
        return cls


class BaseApiView(metaclass=ApiViewMeta):
    def __verify_method_classes(self):
        for method in self.allowed_methods:
            cls = getattr(self, method)
            if not cls.type_ or not isinstance(cls.type_, str):
                raise ImproperlyConfigured(
                    'Wrong resource type on class %s' % method
                )
            func = getattr(self, 'verify_%s_class' % method, None)
            if func:
                func()

    def handle(self, req, resp, handler, *args, **kwargs):
        # TODO: Verify if this cannot be static
        body = handler().run(req, *args, **kwargs)
        resp.text = self.prepare_body(body)
        resp.status = falcon.HTTP_200

    def prepare_body(self, body):
        return json.dumps(body, cls=DateTimeToISOEncoder)

    class Meta:
        abstract = True


class RetrieveView(BaseApiView):
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)


class CreateView(BaseApiView):
    def verify_POST_class(self):
        if not (hasattr(self.POST, 'database_model') and isinstance(self.POST.database_model, Model)):
            raise ImproperlyConfigured(
                'Wrong or missing document object'
            )

    def on_post(self, request, response, *args, **kwargs):
        self.handle(request, response, self.POST, *args, **kwargs)


class UpdateView(BaseApiView):
    def verify_PUT_class(self):
        if not (hasattr(self.PUT, 'database_model') and isinstance(self.PUT.database_model, Model)):
            raise ImproperlyConfigured(
                'Wrong or missing document object'
            )

    def on_put(self, request, response, *args, **kwargs):
        self.handle(request, response, self.PUT, *args, **kwargs)


class SearchView(RetrieveView):
    def verify_GET_class(self):
        if not (hasattr(self.GET, 'search_document') and isinstance(self.GET.search_document, Document)):
            raise ImproperlyConfigured(
                'Wrong or missing document object'
            )


class RetrieveOneView(RetrieveView):
    def verify_GET_class(self):
        if not (hasattr(self.GET, 'database_model') and isinstance(self.GET.database_model, Model)):
            raise ImproperlyConfigured(
                'Wrong or missing database model object'
            )


class RemoveView(BaseApiView):
    def verify_DELETE_class(self):
        if not (hasattr(self.DELETE, 'database_model') and isinstance(self.DELETE.database_model, Model)):
            raise ImproperlyConfigured(
                'Wrong or missing document object'
            )

    def on_delete(self, request, response, *args, **kwargs):
        self.handle(request, response, self.DELETE, *args, **kwargs)
