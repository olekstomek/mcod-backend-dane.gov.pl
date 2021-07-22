from django.utils.module_loading import autodiscover_modules


def autodiscover():
    autodiscover_modules('sparql_graphs')


default_app_config = 'mcod.core.apps.CoreConfig'
