import falcon
from django.db import connection
from django.utils.translation import gettext_lazy as _

from mcod.core.api.search.helpers import extract_script_field
from mcod.lib.handlers import SearchHandler, RetrieveOneHandler
from mcod.lib.triggers import LoginRequired, LoginOptional


class FollowedListHandler(SearchHandler):
    triggers = [LoginRequired(), ]

    def _queryset(self, cleaned, user_id, *args, **kwargs):
        queryset = super()._queryset(cleaned, *args, **kwargs)
        return queryset.filter('term', users_following=str(user_id))

    def _data(self, request, cleaned, *args, **kwargs):
        queryset = self._get_queryset(cleaned, *args, user_id=request.user.id, **kwargs)
        return self._search(queryset, cleaned, *args, **kwargs)


class FollowingSearchHandler(SearchHandler):
    triggers = [LoginOptional(), ]

    def _queryset(self, cleaned, user_id, *args, **kwargs):
        queryset = super()._queryset(cleaned, *args, **kwargs)

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
        user_id = user.id if user else None
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

        return {
            'resource': obj,
            'follower': request.user
        }

    def _data(self, request, cleaned, *args, **kwargs):
        return self.FollowedObject(**cleaned)


class CreateFollowingHandler(RetrieveOneFollowHandler):
    triggers = [LoginRequired(), ]

    def _clean(self, request, *args, **kwargs):
        resource_id = kwargs['id']
        try:
            resource = self.resource_model.objects.get(pk=resource_id)
        except self.resource_model.DoesNotExist:
            raise falcon.HTTPNotFound

        if getattr(request.user, f'followed_{self.resource_name}s').filter(pk=resource.id).exists():
            raise falcon.HTTPForbidden(
                title='403 Forbidden',
                description=_('resource already followed'),
                code='already_followed'
            )

        return {
            'follower': request.user,
            'resource': resource
        }

    def _data(self, request, cleaned, *args, **kwargs):
        following = self.database_model(**{
            'follower': cleaned['follower'],
            self.resource_name: cleaned['resource']
        })
        connection.cursor().execute(
            'SET myapp.userid = "{}"'.format(request.user.id)
        )
        following.save()
        return super()._data(request, cleaned, *args, **kwargs)


class DeleteFollowingHandler(RetrieveOneFollowHandler):
    triggers = [LoginRequired(), ]

    def _clean(self, request, *args, **kwargs):
        resource_id = kwargs['id']
        try:
            resource = self.resource_model.objects.get(pk=resource_id)
        except self.resource_model.DoesNotExist:
            raise falcon.HTTPNotFound

        if not getattr(request.user, f'followed_{self.resource_name}s').filter(pk=resource.id).exists():
            raise falcon.HTTPNotFound(
                title='404 not found',
                description=_('resource is not followed'),
                code='not_followed'
            )
        return {
            'follower': request.user,
            'resource': resource
        }

    def _data(self, request, cleaned, *args, **kwargs):
        following = self.database_model.objects.get(**{
            'follower': cleaned['follower'],
            self.resource_name: cleaned['resource']
        })
        connection.cursor().execute(
            'SET myapp.userid = "{}"'.format(request.user.id)
        )
        following.delete()
        return super()._data(request, cleaned, *args, **kwargs)
