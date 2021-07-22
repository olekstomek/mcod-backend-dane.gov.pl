import pytest
import requests_mock
from django.conf import settings
from falcon.util.structures import Context
from mcod.core.tests.fixtures.bdd import *  # noqa
from mcod.core.tests.fixtures.categories import *  # noqa
from mcod.core.tests.fixtures.harvester import *  # noqa
from mcod.core.tests.fixtures.legacy import *  # noqa
from mcod.core.tests.fixtures.licenses import *  # noqa
from mcod.core.tests.fixtures.newsletter import *  # noqa
from mcod.core.tests.fixtures.tags import *  # noqa
from mcod.core.tests.fixtures.users import *  # noqa
from mcod.core.tests.fixtures.dcat_vocabularies import *  # noqa
from mcod.core.tests.fixtures.rdf import *  # noqa
from mcod.core.tests.fixtures.suggestions import *  # noqa
from mcod.lib.triggers import session_store

adapter = requests_mock.Adapter()


def pytest_configure(config):
    # from elasticsearch import Elasticsearch as ES
    # es_client = ES(hosts=settings.ELASTICSEARCH_HOSTS.split(','))

    # es_client.indices.delete(
    #     index='test-*',
    #     allow_no_indices=True,
    #     expand_wildcards='all',
    #     ignore_unavailable=True
    # )

    config.addinivalue_line(
        "markers", "elasticsearch: mark test to run with new empty set of indicies"
    )


def pytest_sessionstart(session):
    from mcod.resources.link_validation import session
    session.mount('http://test.mcod', adapter)


def pytest_sessionfinish(session):
    pass


def pytest_runtest_setup(item):
    from django_elasticsearch_dsl.registries import registry
    from mcod.core.api.rdf.registry import registry as rdf_registry
    from elasticsearch_dsl.mapping import Mapping
    import random
    import string

    es_marker = item.get_closest_marker('elasticsearch')

    if es_marker:
        common_idx_name = settings.ELASTICSEARCH_INDEX_NAMES['common']
        for index in registry.get_indices():
            index.delete(ignore=404)
            index.settings(**settings.ELASTICSEARCH_DSL_INDEX_SETTINGS)
            if index._name == 'common':
                common_mapping = Mapping('doc')
                common_docs = [doc for doc in registry.get_documents() if doc.Index.name == common_idx_name]
                for doc in common_docs:
                    common_mapping.update(doc._doc_type.mapping)
                index.mapping = common_mapping
            index.create()

    sparql_marker = item.get_closest_marker('sparql')
    if sparql_marker:
        chars = string.ascii_uppercase + string.ascii_lowercase
        graph_name = ''.join(random.choice(chars) for _ in range(18))
        graph_uri = f'<http://test.mcod/{graph_name}>'
        rdf_registry.create_named_graph(graph_uri)

    # redis_marker = item.get_closest_marker('redis')
    # if redis_marker:
    #     redis_client = get_redis_connection()
    #     redis_client.flushall()


def pytest_runtest_teardown(item, nextitem):
    from mcod.core.api.rdf.registry import registry as rdf_registry
    from django_elasticsearch_dsl.registries import registry

    es_marker = item.get_closest_marker('elasticsearch')
    if es_marker:
        for index in registry.get_indices():
            index.delete(ignore=404)

    sparql_marker = item.get_closest_marker('sparql')
    if sparql_marker:
        rdf_registry.delete_named_graph()


@pytest.fixture(autouse=True)
def enable_db_access(db):
    pass


@pytest.fixture
def context():
    _context = Context()
    _context.obj = {}
    _context.api = Context()
    _context.api.headers = {
        'Accept-Language': 'pl',
        'Content-Type': 'application/vnd.api+json'
    }
    _context.api.cookies = {}

    _context.api.method = 'GET'
    _context.api.path = '/'
    _context.api.params = {}
    _context.api.body = {}
    _context.user = None
    _context.session = session_store()
    return _context


@pytest.fixture
def admin_context(admin):
    _context = Context()
    _context.obj = {}
    _context.admin = Context()
    _context.admin.headers = {
        'Accept-Language': 'pl',
    }

    _context.admin.method = 'GET'
    _context.admin.path = '/'
    _context.admin.user = admin
    _context.admin.params = {}
    _context.admin.body = {}
    _context.user = None
    _context.session = session_store()
    return _context
