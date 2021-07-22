import decorator
from django.core.cache import caches

from mcod import settings

marker = object()


def _memoize(func, *args, **kw):
    cache = getattr(func, '_cache', marker)
    if cache is marker:
        func._cache = func(*args, **kw)
        return func._cache
    else:
        return cache


def memoize(f):
    return decorator.decorator(_memoize, f)


def flush_sessions():
    _cache = caches[settings.SESSION_CACHE_ALIAS]
    _cache.delete_pattern('*')


def flush_cache(cache='default'):
    _cache = caches[cache]
    _cache.delete_pattern('*')
