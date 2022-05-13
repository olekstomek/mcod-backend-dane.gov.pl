from urllib.parse import urlparse

from django.conf import settings


def get_base_url(request=None):
    base_url = getattr(settings, 'CMS_URL', request.site.root_url if request and request.site else None)

    if base_url:
        # We only want the scheme and netloc
        base_url_parsed = urlparse(base_url)
        return base_url_parsed.scheme + '://' + base_url_parsed.netloc


def get_full_url(request, path):
    path = path.replace('//', '/')
    base_url = get_base_url(request) or ''
    return base_url + path


def get_object_detail_url(router, request, model, url_path):
    url_path = router.get_object_detail_urlpath(model, url_path)

    if url_path:
        return get_full_url(request, url_path)
