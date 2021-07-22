import datetime

import pytest
from namedlist import namedlist

from mcod.datasets.forms import DatasetForm
from mcod.datasets.models import Dataset
from mcod.lib.helpers import change_namedlist
from mcod.unleash import is_enabled

fields = [
    'slug',
    'title',
    'url',
    'notes',
    'license_id',
    'organization',
    'customfields',
    'license_condition_db_or_copyrighted',
    'license_condition_personal_data',
    'license_condition_modification',
    'license_condition_original',
    'license_condition_responsibilities',
    'license_condition_source',
    'update_frequency',
    'legacy_category',
    'status',
    'validity'
]

entry = namedlist('entry', fields)

empty = entry(
    slug=None,
    title=None,
    url=None,
    notes=None,
    license_id=None,
    organization=None,
    customfields=None,
    license_condition_db_or_copyrighted=None,
    license_condition_personal_data=None,
    license_condition_modification=None,
    license_condition_original=None,
    license_condition_responsibilities=None,
    license_condition_source=None,
    update_frequency=None,
    legacy_category=None,
    status=None,
    validity=False,
)

minimal = change_namedlist(empty, {
    'title': "Dataset title",
    'notes': 'dataset description',
    'slug': "test",
    'url': 'http://cos.tam.pl',
    'update_frequency': "weekly",
    'organization': None,
    'license_id': "other-pd",
    'status': 'published',
    'validity': True
})


class TestDatasetFormValidity:
    """
    """

    @pytest.mark.parametrize(
        ", ".join(fields),
        [
            # correct scenarios
            minimal,
            # full,
            #
            # incorect scenarios
            # title
            #   no title
            change_namedlist(minimal, {'title': None, 'validity': False}),
            #   too long
            change_namedlist(minimal, {'title': "T" * 301, 'validity': False}),
            # name                *   auto/manual - base on title
            #   no name
            change_namedlist(minimal, {'title': 'no slug', 'slug': None, 'validity': True}),
            # #   too long name
            # change_namedlist(minimal, {'title': 'too long name', 'slug': "T" * 601, 'validity': True}),
            # category
            #   wrong category
            change_namedlist(minimal, {'legacy_category': 'xxx', 'validity': False}),
            # status               *   choices
            #   No status choice
            change_namedlist(minimal, {'title': 'no status', 'status': None, 'validity': False}),
            #   wrong choice value of status
            change_namedlist(minimal, {'title': 'wrong status', 'status': "XXX", 'validity': False}),
            # private
            # metadata_modified
            # creator_user_id     *   auto
            # url
            # wrong url format
            change_namedlist(minimal, {'title': 'wrong app_url format', 'url': "wrong format", 'validity': False}),

        ])
    def test_dataset_form_validity(self,
                                   slug,
                                   title,
                                   url,
                                   notes,
                                   license_id,
                                   organization,
                                   customfields,
                                   license_condition_db_or_copyrighted,
                                   license_condition_personal_data,
                                   license_condition_modification,
                                   license_condition_original,
                                   license_condition_responsibilities,
                                   license_condition_source,
                                   update_frequency,
                                   legacy_category,
                                   status,
                                   validity,
                                   institution,
                                   tag,
                                   tag_pl
                                   ):
        data = {
            "slug": slug,
            "title": title,
            "url": url,
            "notes": notes,
            "license_id": license_id,
            "organization": institution.id,
            "customfields": customfields,
            "license_condition_db_or_copyrighted": license_condition_db_or_copyrighted,
            "license_condition_personal_data": license_condition_personal_data,
            "license_condition_modification": license_condition_modification,
            "license_condition_original": license_condition_original,
            "license_condition_responsibilities": license_condition_responsibilities,
            "license_condition_source": license_condition_source,
            "update_frequency": update_frequency,
            "category": legacy_category,
            "status": status,
        }
        if is_enabled('S18_new_tags.be'):
            data['tags_pl'] = [tag_pl.id]
        else:
            data['tags'] = [tag.id]

        form = DatasetForm(data=data)
        assert form.is_valid() is validity

        if validity and title != "no name":
            form.save()
            assert Dataset.objects.last().title == title
        # if title == "no name":
        #     with pytest.raises(ValidationError) as e:
        #         form.save()
        #     # assert "'slug'" in str(e.value)

    def test_dataset_form_add_tags(self, tag, tag_pl, tag_en, institution):
        data = {
            'title': "Test add tag",
            'slug': "test-add-tag",
            'status': 'published',
            'organization': institution.id,
            'notes': "notes",
            "update_frequency": "weekly",
            'url': "http://cos.tam.pl",
        }
        if is_enabled('S18_new_tags.be'):
            data['tags_pl'] = [tag_pl]
            data['tags_en'] = [tag_en]
        else:
            data['tags'] = [tag]

        form = DatasetForm(data=data)
        assert form.is_valid()
        form.save()
        dataset = Dataset.objects.last()
        assert dataset.slug == "test-add-tag"

        if is_enabled('S18_new_tags.be'):
            assert tag_pl in dataset.tags.all()
            assert tag_en in dataset.tags.all()
        else:
            assert tag in dataset.tags.all()

    def test_dataset_form_add_categories(self, categories, tag, tag_pl, institution):
        data = {
            'title': "Test add categories",
            'slug': "test-add-categories",
            'status': 'published',
            'organization': institution.id,
            'notes': "notes",
            "update_frequency": "weekly",
            'url': "http://cos.tam.pl",
            'categories': [category.id for category in categories]
        }
        if is_enabled('S18_new_tags.be'):
            data['tags_pl'] = [tag_pl]
        else:
            data['tags'] = [tag]

        form = DatasetForm(data=data)
        assert form.is_valid()
        form.save()
        dataset = Dataset.objects.last()
        assert all(category in dataset.categories.all() for category in categories)

    def test_metadata_modified_is_not_null(self, institution, tag, tag_pl):
        data = {
            'title': "test metadata_modified title",
            'slug': "Test",
            'notes': 'dataset notes',
            'organization': institution.id,
            'url': 'http://cos.tam.pl',
            'update_frequency': "weekly",
            'license_id': "other-pd",
            'status': 'published',
            'validity': True,
        }
        if is_enabled('S18_new_tags.be'):
            data['tags_pl'] = [tag_pl.id]
        else:
            data['tags'] = [tag.id]

        form = DatasetForm(data=data)
        assert form.is_valid()
        form.save()
        last_ds = Dataset.objects.last()
        assert last_ds.title == data['title']
        assert isinstance(last_ds.modified, datetime.datetime)

    def test_add_category(self, institution, legacy_category, tag, tag_pl):
        data = {
            'title': "Test add tag",
            'slug': "test-add-tag",
            'status': 'published',
            'organization': institution.id,
            'notes': "notes",
            "update_frequency": "weekly",
            'url': "http://cos.tam.pl",
            'category': legacy_category.id,
        }
        if is_enabled('S18_new_tags.be'):
            data['tags_pl'] = [tag_pl.id]
        else:
            data['tags'] = [tag.id]

        form = DatasetForm(data=data)
        form.is_valid()
        assert form.is_valid()
        form.save()
        d = Dataset.objects.last()
        assert d.slug == 'test-add-tag'
        assert d.category == legacy_category

    def test_is_valid_upload_image(self, institution, tag, tag_pl, small_image):
        data = {
            'title': "Test add tag",
            'slug': "test-add-tag",
            'status': 'published',
            'organization': institution.id,
            'notes': "notes",
            "update_frequency": "weekly",
            'url': "http://cos.tam.pl",
        }
        if is_enabled('S18_new_tags.be'):
            data['tags_pl'] = [tag_pl.id]
        else:
            data['tags'] = [tag.id]
        form = DatasetForm(data=data, files={'image': small_image})
        assert form.is_valid()
