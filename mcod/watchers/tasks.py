from celery import shared_task


@shared_task
def watcher_updated_task(watcher_id, prev_value, obj_state):
    pass


@shared_task
def query_watcher_created_task(watcher_id, created_at=None):
    pass

#     @staticmethod
#     def obj_to_data(url, headers=None):
#         scheme, netloc, path, query, fragment = urlsplit(url)
#         view = app._router_search(path.strip('/'))
#         if not view:
#             raise Exception('No handler for this url.')
#         _scheme, _netloc, __, __ = urlsplit(settings.API_URL)
#         if scheme != _scheme or netloc != _netloc:
#             raise Exception('Invalid url address.')
#         if query:
#             query = parser.parse(query)
#
#         return {
#             'scheme': scheme,
#             'netloc': netloc,
#             'path': path,
#             'query': query or {},
#             'headers': headers or {}
#         }
#
#     @staticmethod
#     def data_to_obj(data):
#         if not any('schema', 'netloc', 'path', 'query', 'headers') in data:
#             raise Exception('invalid data')
#
#         url = '{}://{}/{}'.format(data['schema'], data['netloc'], data['path'])
#         params = data['query']
#         params['page'] = 1
#         params['per_page'] = 1
#         return url, params, data['headers']
#
#     def run(self, request=None):
#         url, params, headers = self.data_to_obj(self.data)
#         try:
#             result = requests.get(url, params=params, headers=headers)
#             if result.status_code != 200:
#                 raise requests.exceptions.RequestException
#         except requests.exceptions.RequestException:
#             raise Exception('Network error, could not get response')
#
#         if result.headers['Content-Type'] != 'application/vnd.api+json':
#             raise Exception('Invalid response content-type')
#
#         data = result.json()
#         try:
#             new_value = data['meta']['count']
#         except KeyError:
#             raise Exception('Invalid response format.')
#
#         prev_value = self.ref_value.get('count', 0) if self.ref_value else 0
#
#         if new_value != prev_value:
#             self.ref_value = {
#                 'count': new_value
#             }
#
#             self.last_ref_change = now()
#             self.save()
#
#             watcher_updated.send(self, prev_value, new_value)
