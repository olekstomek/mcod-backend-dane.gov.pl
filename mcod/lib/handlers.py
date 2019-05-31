# -*- coding: utf-8 -*-

import falcon
from elasticsearch import TransportError
from falcon.util import to_query_str

from mcod import settings
from mcod.histories.models import History
from mcod.core.api.parsers import Parser


class BaseHandler:
    def __init__(self, request, response):
        self.request = request
        self.response = response

    def run(self, *args, **kwargs):
        request = self.request
        cleaned = self._clean(request, *args, **kwargs)
        explain = cleaned.get('explain', None) if isinstance(cleaned, dict) else None
        data = self._data(request, cleaned, *args, explain=explain, **kwargs)
        if explain == '1':
            return data
        meta = self._metadata(request, data, *args, **kwargs)
        links = self._links(request, data, *args, **kwargs)
        return self._serialize(data, meta, links, *args, **kwargs)

    def _clean(self, request, *args, locations=None, **kwargs):
        locations = locations or ('headers', 'query')
        return Parser(locations=locations).parse(self.deserializer_schema, req=request)

    def _data(self, request, cleaned, *args, **kwargs):
        return cleaned

    def _metadata(self, request, data, *args, **kwargs):
        ms = getattr(self, 'meta_serializer', None)
        meta = ms.dump(data) if ms else {}

        meta.update(
            {
                'language': request.language,
                'params': request.params,
                'path': request.path,
                'rel_uri': request.relative_uri,
            }
        )

        return meta

    @staticmethod
    def _link(path, params):
        return '{}{}'.format(path, to_query_str(params))

    def _links(self, request, data, *args, **kwargs):
        return {'self': self._link(request.path, request.params)}

    def _serialize(self, data, meta, links=None, *args, **kwargs):
        res = self.serializer_schema.dump(data, meta, links)
        return res


class ListHandler(BaseHandler):
    def _links(self, request, data, *args, **kwargs):
        links = self._pagination_links(request, count=len(data))
        links['self'] = self._link(request.path, request.params)
        return links

    def _pagination_links(self, request, count=None):
        def _link_for_page(page, path, params):
            params = dict(params)
            params['page'] = page
            return self._link(path, params)

        links = {}
        req_page = int(request.params.setdefault('page', 1))
        req_per_page = int(request.params.setdefault('per_page', settings.PER_PAGE_DEFAULT))
        links['first'] = _link_for_page(1, request.path, request.params)
        if req_page > 1:
            links['prev'] = _link_for_page(req_page - 1, request.path, request.params)
        if count:
            mod = 1 if count % req_per_page else 0
            last_page = count // req_per_page + mod
            if last_page > 1:
                links['last'] = _link_for_page(last_page, request.path, request.params)

            if req_page * req_per_page < count:
                links['next'] = _link_for_page(req_page + 1, request.path, request.params)

        return links


class SearchHandler(ListHandler):
    def _data(self, request, cleaned, *args, **kwargs):
        queryset = self._get_queryset(cleaned, *args, **kwargs)
        return self._search(queryset, cleaned, *args, **kwargs)

    def _queryset(self, cleaned, *args, **kwargs):
        queryset = self.search_document.search()
        for name, field in self.deserializer_schema.fields.items():
            queryset = field.prepare_queryset(queryset, context=cleaned.get(name, None))
        return queryset

    def _get_queryset(self, cleaned, **kwargs):
        queryset = self._queryset(cleaned, **kwargs)
        page, per_page = cleaned.get('page', 1), cleaned.get('per_page', 20)
        start = (page - 1) * per_page
        qs = queryset[start:start + per_page]
        return qs

    def _search(self, queryset, cleaned, *args, explain=None, **kwargs):
        if explain == '1':
            return queryset.to_dict()

        try:
            data = queryset.execute()
            return data
        except TransportError as err:
            raise falcon.HTTPBadRequest(description=err.info['error']['reason'])


class RetrieveOneHandler(BaseHandler):
    def _clean(self, request, id, *args, **kwargs):
        model = self.database_model
        try:
            return model.objects.get(pk=id)
        except model.DoesNotExist:
            raise falcon.HTTPNotFound


class RetrieveHistoryHandler(BaseHandler):
    def _clean(self, request, id, *args, **kwargs):
        try:
            return History.objects.filter(table_name=self.table_name, row_id=id).order_by('-id')
        except History.DoesNotExist:
            raise falcon.HTTPNotFound


class CreateHandler(BaseHandler):
    def _clean(self, request, *args, **kwargs):
        return super()._clean(request, *args, locations=('json', 'headers'), **kwargs)


class UpdateHandler(CreateHandler):
    pass
