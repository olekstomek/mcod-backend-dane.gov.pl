import pytest


@pytest.mark.django_db
class TestSystemInfos:
    def test_str(self, valid_tag):
        assert str(valid_tag) == valid_tag.name
