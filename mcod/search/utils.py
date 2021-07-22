from django_elasticsearch_dsl.registries import registry

from mcod import settings
from mcod.unleash import is_enabled


def register_legacy_document(document):
    if is_enabled('S24_es_documents_unification.be'):
        return document
    return registry.register_document(document)


def register_unified_document(document):
    if is_enabled('S24_es_documents_unification.be'):
        return registry.register_document(document)
    return document


def get_active_document(unified_document, legacy_document):
    if is_enabled('S24_es_documents_unification.be'):
        return unified_document
    return legacy_document


def search_index_name():
    if is_enabled('S24_es_documents_unification.be'):
        return settings.ELASTICSEARCH_COMMON_ALIAS_NAME
    return settings.ELASTICSEARCH_COMMON_INDEX_NAME
