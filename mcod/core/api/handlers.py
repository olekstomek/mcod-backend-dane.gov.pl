# -*- coding: utf-8 -*-

import falcon
from elasticsearch import TransportError
from marshmallow import ValidationError
from querystring_parser.parser import MalformedQueryStringError

from mcod.core.api.parsers import Parser


class BaseHdlr:
    def __init__(self, request, response):
        self.request = request
        self.response = response
        self.deserializer = self.deserializer_schema(context={
            'request': self.request,
        })
        self.serializer = self.serializer_schema(context={
            'request': self.request,
        })

    def run(self, *args, **kwargs):
        self.request.context.cleaned_data = self.clean(*args, **kwargs)
        return self.serialize(*args, **kwargs)

    def clean(self, *args, validators=None, locations=None, **kwargs):
        locations = locations or ('query',)
        try:
            result = Parser(
                locations=locations,
            ).parse(
                self.deserializer,
                req=self.request,
                validate=validators
            )
            return result
        except MalformedQueryStringError:
            raise falcon.HTTPBadRequest(description="malformed query string")

    def prepare_context(self, *args, **kwargs):
        cleaned = getattr(self.request.context, 'cleaned_data') or {}
        debug_enabled = getattr(self.response.context, 'debug', False)
        if debug_enabled:
            self.response.context.query = self._get_debug_query(cleaned, *args, **kwargs)
        result = self._get_data(cleaned, *args, **kwargs)
        if result:
            self.response.context.data = result
            self.response.context.meta = self._get_meta(result, *args, **kwargs)
            included = self._get_included(result, *args, **kwargs)
            if included:
                self.response.context.included = included

    def serialize(self, *args, **kwargs):
        self.prepare_context(*args, **kwargs)
        return self.serializer.dump(self.response.context)

    def _get_data(self, cleaned, *args, **kwargs):
        return cleaned

    def _get_meta(self, cleaned, *args, **kwargs):
        return {}

    def _get_included(self, cleaned, *args, **kwargs):
        return []

    def _get_debug_query(self, cleaned, *args, **kwargs):
        return {}


class SearchHdlr(BaseHdlr):
    def _queryset_extra(self, queryset, *args, **kwargs):
        return queryset

    def _get_queryset(self, cleaned, *args, **kwargs):
        queryset = self.search_document.search()
        queryset = self.deserializer.get_queryset(queryset, cleaned)
        queryset = self._queryset_extra(queryset, *args, **kwargs)
        page, per_page = cleaned.get('page', 1), cleaned.get('per_page', 20)
        start = (page - 1) * per_page
        return queryset.extra(from_=start, size=per_page)

    def _get_debug_query(self, cleaned, *args, **kwargs):
        qs = self._get_queryset(cleaned, *args, **kwargs)
        return qs.to_dict()

    def _get_data(self, cleaned, *args, **kwargs):
        queryset = self._get_queryset(cleaned, *args, **kwargs)
        try:
            return queryset.execute()
        except TransportError as err:
            raise falcon.HTTPBadRequest(description=err.info['error']['reason'])


class RetrieveManyHdlr(BaseHdlr):
    def _get_queryset(self, cleaned, *args, **kwargs):
        return self.database_model.objects.all()

    def _get_debug_query(self, cleaned, *args, **kwargs):
        queryset = self._get_queryset(cleaned, *args, **kwargs)
        return queryset.query


class RetrieveOneHdlr(BaseHdlr):
    def _get_instance(self, id, *args, **kwargs):
        instance = getattr(self, '_cached_instance', None)
        if not instance:
            model = self.database_model
            try:
                self._cached_instance = model.objects.get(pk=id)
            except model.DoesNotExist:
                raise falcon.HTTPNotFound
        return self._cached_instance

    def clean(self, id, *args, **kwargs):
        self._get_instance(id, *args, **kwargs)
        return {}

    def _get_data(self, cleaned, id, *args, **kwargs):
        return self._get_instance(id, *args, **kwargs)


class CreateOneHdlr(BaseHdlr):
    def clean(self, *args, **kwargs):
        return super().clean(*args, locations=('headers', 'json'), **kwargs)

    def _get_data(self, cleaned, *args, **kwargs):
        model = self.database_model
        data = cleaned['data']['attributes']
        self.response.context.data = model.create(**data)


class UpdateOneHdlr(BaseHdlr):
    def clean(self, id, *args, **kwargs):
        def validate_id(data):
            if data['data']['id'] != str(id):
                raise ValidationError({'data': {'id': ['Invalid value']}})
            return True

        return super().clean(*args, locations=('headers', 'json'), validators=[validate_id, ], **kwargs)

    def _get_data(self, cleaned, *args, **kwargs):
        data = cleaned['data']['attributes']
        model = self.database_model
        try:
            instance = model.objects.get(pk=id)
        except model.DoesNotExist:
            raise falcon.HTTPNotFound

        for key, val in data:
            setattr(instance, key, val)
        instance.save(update_fields=list(data.keys()))
        instance.refresh_from_db()
        return instance


class RemoveOneHdlr(BaseHdlr):
    def clean(self, id, *args, **kwargs):
        model = self.database_model
        try:
            return model.objects.get(pk=id)
        except model.DoesNotExist:
            raise falcon.HTTPNotFound

    def _get_data(self, cleaned, id, *args, **kwargs):
        cleaned.delete()
        return {}
