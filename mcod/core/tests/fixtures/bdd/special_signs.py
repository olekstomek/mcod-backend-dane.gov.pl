import pytest
from mcod.special_signs.factories import SpecialSignFactory


@pytest.fixture
def special_sign():
    return SpecialSignFactory.create()
