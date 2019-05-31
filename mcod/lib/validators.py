import json
import falcon


class RequestValidator(object):
    __parsers__ = {
        'json': 'parse_json',
        'querystring': 'parse_querystring',
        'query': 'parse_querystring',
        'form': 'parse_form',
        'headers': 'parse_headers',
        'cookies': 'parse_cookies',
        'files': 'parse_files',
    }

    def __init__(self, form_class, locations, request, **kwargs):
        data = self.prepare_data(locations, request)
        self.form = form_class(data=data, **kwargs)

    def prepare_data(self, locations, req):
        data = {}
        for location in locations:
            func = getattr(self, self.__parsers__.get(location))
            data.update(func(req))

        return data

    def validate(self):
        self.form.is_valid()
        return self.form.cleaned_data, self.form.errors

    def parse_json(self, req):
        if req.content_length in (None, 0):
            return {}

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            data = json.loads(body.decode('utf-8'))
            return data
        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def parse_querystring(self, req):
        return req.params

    def parse_form(self, req):
        raise NotImplementedError()

    def parse_headers(self, req):
        return req.headers

    def parse_cookies(self, req):
        return req.cookies

    def parse_files(self, req):
        raise NotImplementedError()
