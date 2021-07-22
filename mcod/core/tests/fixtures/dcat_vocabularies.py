import pytest
from mcod.lib.dcat.vocabularies.manager import VocabulariesManager


@pytest.fixture
def vocabularies_manager():
    return VocabulariesManager('TestModel')
