import pytest

from mcod.tags.forms import TagForm


@pytest.mark.django_db
def test_form_validates_tag_exists(valid_tag):
    form = TagForm(data={'name': 'TEST'})
    assert not form.is_valid()


@pytest.mark.django_db
def test_form_validates_tag_is_valid():
    form = TagForm(data={'name': 'TEST12'})
    assert form.is_valid()
