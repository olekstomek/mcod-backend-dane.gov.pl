import logging

import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

logger = logging.getLogger('mcod')


class BaseApi:

    def __init__(self, url):
        self.url = url
        self.user = settings.GEOCODER_USER
        self.password = settings.GEOCODER_PASS

    def _send_request(self, api_path, params, err_resp=None):
        url = f"{self.url}{api_path}"
        try:
            resp = requests.get(url, params=params, auth=HTTPBasicAuth(self.user, self.password)).json()
        except requests.exceptions.RequestException as err:
            resp = err_resp if err_resp is not None else []
            logger.error('Error occurred while sending request by {} to url {} with params {} : {}'.format(
                self.__class__.__name__, url, params, err
            ))
        return resp


class PlaceholderApi(BaseApi):

    def __init__(self):
        super(PlaceholderApi, self).__init__(settings.PLACEHOLDER_URL)

    def find_by_id(self, ids):
        params = {'ids': ','.join([str(i) for i in ids])}
        resp = self._send_request('/parser/findbyid', params, err_resp={})
        return resp


class PeliasApi(BaseApi):

    def __init__(self, size=25):
        self.size = size
        super(PeliasApi, self).__init__(settings.GEOCODER_URL + '/v1/')

    def autocomplete(self, text, lang='pl', layers=None):
        params = {'text': text,
                  'lang': lang,
                  'sources': 'wof',
                  'size': self.size}
        if layers:
            params['layers'] = layers
        return self._send_request('autocomplete', params)

    def place(self, ids):
        params = {
            'ids': ','.join(ids)
        }
        return self._send_request('place', params, err_resp={})
