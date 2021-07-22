from django.utils.deprecation import MiddlewareMixin

from wagtail.core.models import Site


class SiteMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            request.site = Site.find_for_request(request)
        except Site.DoesNotExist:
            request.site = None
