from elasticsearch_dsl.query import Q

from mcod.core.api.search.helpers import extract_script_field
from mcod.lib.handlers import SearchHandler, RetrieveOneHandler
from mcod.lib.triggers import LoginOptional


class FollowingSearchHandler(SearchHandler):
    triggers = [LoginOptional(), ]

    def _queryset(self, cleaned, user_id, *args, **kwargs):
        queryset = super()._queryset(cleaned, *args, **kwargs)
        queryset = queryset.source(exclude=['subscription*'])
        if user_id:
            queryset = queryset.filter(Q('bool', should=[
                Q('nested', path='subscriptions',
                  query=Q('match', **{"subscriptions.user_id": user_id}), inner_hits={}),
                Q('match_all')
            ]))
        script = {
            'script': {
                'source': "return doc['users_following'].contains(params.user_id);",
                'params': {'user_id': str(user_id)}
            }
        }
        queryset = queryset.extra(stored_fields=['_source']).script_fields(followed=script)
        return queryset

    def _data(self, request, cleaned, *args, **kwargs):
        user = getattr(request, 'user', None)
        user_id = user.id if user and user.is_authenticated else None
        queryset = self._get_queryset(cleaned, *args, user_id=user_id, **kwargs)
        search = self._search(queryset, cleaned, *args, **kwargs)
        if cleaned['explain'] != '1':
            extract_script_field(search, 'followed')
        return search


class RetrieveOneFollowHandler(RetrieveOneHandler):
    class FollowedObject(object):
        def __init__(self, resource, follower):
            self.resource = resource
            self.follower = follower

        def __getattr__(self, item):
            if item == 'followed':
                return self.resource.users_following.filter(pk=self.follower.id).exists()
            else:
                return getattr(self.resource, item)

    def _clean(self, request, id, *args, **kwargs):
        if hasattr(self, 'resource_clean'):
            obj = self.resource_clean(request, id, *args, **kwargs)
        else:
            obj = super()._clean(request, id, *args, **kwargs)

        user = request.user if request.user.is_authenticated else None
        if user:
            obj.set_subscription(user)
        return {
            'resource': obj,
            'follower': request.user
        }

    def _data(self, request, cleaned, *args, **kwargs):
        d = self.FollowedObject(**cleaned)

        return d
