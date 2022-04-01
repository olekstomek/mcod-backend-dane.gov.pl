from django import VERSION


def is_django_ver_lt(major=2, minor=2):
    return VERSION[0] < major or (VERSION[0] == major and VERSION[1] < minor)
