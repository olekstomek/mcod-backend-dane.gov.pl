from mcod.tags.forms import TagForm
from mcod.unleash import is_enabled


def test_form_doesnt_validate_if_tag_exists(tag, tag_pl):
    if is_enabled('S18_new_tags.be'):
        data = {
            'name': tag_pl.name,
            'language': tag_pl.language,
        }
    else:
        data = {'name': tag.name}
    form = TagForm(data=data)
    assert not form.is_valid()


def test_form_validates_tag_is_valid():
    data = {'name': 'TEST12'}
    if is_enabled('S18_new_tags.be'):
        data['language'] = 'pl'
    form = TagForm(data=data)
    assert form.is_valid()


def test_form_validates_if_tag_exists_in_other_language(tag_pl, tag_en):
    data = {'name': tag_pl.name}
    if is_enabled('S18_new_tags.be'):
        data['language'] = tag_en.language
    form = TagForm(data=data)
    assert form.is_valid()
