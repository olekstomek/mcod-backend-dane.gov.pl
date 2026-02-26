from importlib import import_module

from django.conf import settings

session_store = import_module(settings.SESSION_ENGINE).SessionStore
