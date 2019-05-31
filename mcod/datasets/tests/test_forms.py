import datetime

import pytest
from namedlist import namedlist

from mcod.datasets.forms import DatasetForm
from mcod.datasets.models import Dataset
from mcod.lib.helpers import change_namedlist

fields = [
    'slug',
    'title',
    'url',
    'notes',
    'license_id',
    'organization',
    'customfields',
    'license_condition_db_or_copyrighted',
    'license_condition_modification',
    'license_condition_original',
    'license_condition_responsibilities',
    'license_condition_source',
    'update_frequency',
    'category',
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
    license_condition_modification=None,
    license_condition_original=None,
    license_condition_responsibilities=None,
    license_condition_source=None,
    update_frequency=None,
    category=None,
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


@pytest.mark.django_db
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
            change_namedlist(minimal, {'category': 'xxx', 'validity': False}),
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
                                   license_condition_modification,
                                   license_condition_original,
                                   license_condition_responsibilities,
                                   license_condition_source,
                                   update_frequency,
                                   category,
                                   status,
                                   validity,
                                   valid_organization,
                                   valid_tag
                                   ):
        form = DatasetForm(data={
            "slug": slug,
            "title": title,
            "url": url,
            "notes": notes,
            "license_id": license_id,
            "organization": valid_organization.id,
            "customfields": customfields,
            "license_condition_db_or_copyrighted": license_condition_db_or_copyrighted,
            "license_condition_modification": license_condition_modification,
            "license_condition_original": license_condition_original,
            "license_condition_responsibilities": license_condition_responsibilities,
            "license_condition_source": license_condition_source,
            "update_frequency": update_frequency,
            "category": category,
            "status": status,
            "tags": [valid_tag.id, ],
        })
        assert form.is_valid() is validity

        if validity and title != "no name":
            form.save()
            assert Dataset.objects.last().title == title
        # if title == "no name":
        #     with pytest.raises(ValidationError) as e:
        #         form.save()
        #     # assert "'slug'" in str(e.value)

    def test_dataset_form_add_tags(self, valid_tag, valid_organization):
        form = DatasetForm(data={
            'title': "Test add tag",
            'slug': "test-add-tag",
            'status': 'published',
            'organization': valid_organization.id,
            'notes': "notes",
            "update_frequency": "weekly",
            'url': "http://cos.tam.pl",
            'tags': [valid_tag]
        })
        assert form.is_valid()
        form.save()
        ap = Dataset.objects.last()
        assert ap.slug == "test-add-tag"
        assert valid_tag in ap.tags.all()

    def test_metadata_modified_is_not_null(self, valid_organization, valid_tag):
        data = {
            'title': "test metadata_modified title",
            'slug': "Test",
            'notes': 'dataset notes',
            'organization': valid_organization.id,
            'url': 'http://cos.tam.pl',
            'update_frequency': "weekly",
            'license_id': "other-pd",
            'status': 'published',
            'validity': True,
            'tags': [valid_tag.id]
        }
        form = DatasetForm(data=data)
        assert form.is_valid()
        form.save()
        last_ds = Dataset.objects.last()
        assert last_ds.title == data['title']
        assert isinstance(last_ds.modified, datetime.datetime)

    def test_add_valid_category(self, valid_organization, valid_category, valid_tag):
        form = DatasetForm(data={
            'title': "Test add tag",
            'slug': "test-add-tag",
            'status': 'published',
            'organization': valid_organization.id,
            'notes': "notes",
            "update_frequency": "weekly",
            'url': "http://cos.tam.pl",
            'category': valid_category.id,
            'tags': [valid_tag.id]
        })
        form.is_valid()
        assert form.is_valid()
        form.save()
        d = Dataset.objects.last()
        assert d.slug == 'test-add-tag'
        assert d.category == valid_category
