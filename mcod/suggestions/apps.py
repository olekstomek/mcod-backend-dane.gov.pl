from django.apps import AppConfig
from mcod.core.apps import ExtendedAppMixin


class SuggestionsConfig(ExtendedAppMixin, AppConfig):
    name = 'mcod.suggestions'
