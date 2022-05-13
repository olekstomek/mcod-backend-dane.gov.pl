from datetime import date

import pytest
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.db.models.query import QuerySet

from mcod.applications.models import Application


class TestApplicationModel:
    def test_can_not_create_empty_application(self):
        with pytest.raises(ValidationError)as e:
            a = Application()
            a.full_clean()
        assert "'title'" in str(e.value)
        assert "'url'" in str(e.value)
        assert "'notes'" in str(e.value)

    def test_create_application(self):
        a = Application()
        a.slug = "test-name"
        a.title = "Test name"
        a.notes = "Treść"
        a.url = "http://smth.smwheere.com"
        assert a.full_clean() is None
        assert a.id is None
        a.save()
        assert a.id is not None
        assert a.status == "published"

    def test_add_dataset(self, application, dataset):
        application.datasets.set([dataset])
        assert application.full_clean() is None
        application.save()
        app = Application.objects.get(id=application.id)
        assert dataset in app.datasets.all()

    def test_add_tag(self, application, tag):
        application.tags.set([tag])
        assert application.full_clean() is None
        application.save()
        app = Application.objects.get(id=application.id)
        assert tag in app.tags.all()

    def test_application_has_proper_columns_and_relations(self, application):
        app_dict = application.__dict__
        fields = [
            "id",
            "slug",
            "title",
            "notes",
            "author",
            "status",
            "modified",
            "created_by_id",
            "image",
            "created",
            "url",
        ]
        for f in fields:
            assert f in app_dict
        assert isinstance(application.datasets.all(), QuerySet)
        assert isinstance(application.tags.all(), QuerySet)

    def test_safe_delete(self, application):
        assert application.status == 'published'
        application.delete()
        assert application.is_removed is True
        with pytest.raises(ObjectDoesNotExist) as e:
            Application.objects.get(id=application.id)
        assert "Application matching query does not exist." in str(e.value)
        assert Application.raw.get(id=application.id)

    def test_unsafe_delete(self, application):
        assert application.status == 'published'
        application.delete(soft=False)
        with pytest.raises(ObjectDoesNotExist) as e:
            Application.objects.get(id=application.id)
        assert "Application matching query does not exist." in str(e.value)

    def test_image_path_and_url(self, application, small_image):
        application.image = small_image
        application.save()
        application.refresh_from_db()
        assert application.image
        assert application.image_thumb
        date_folder = date.today().isoformat().replace('-', '')
        image_name = application.image.name
        assert application.image.url == f"/media/images/applications/{image_name}"
        assert application.image.path == f"{settings.IMAGES_MEDIA_ROOT}/applications/{image_name}"
        assert date_folder in application.image.url
        assert date_folder in application.image.path

    def test_main_page_position_on_create(self):
        application1 = Application.objects.create(title="test application 1", notes="test description 1")
        assert application1.main_page_position is None, "main page position should be None if not specified"

    def test_main_page_position_no_duplicates(self):
        application1 = Application.objects.create(
            title="test application 1",
            notes="test description 1",
            main_page_position=1
        )
        assert application1.main_page_position == 1

        with pytest.raises(
            IntegrityError
        ):
            Application.objects.create(
                title="test application 2",
                notes="test description 2",
                main_page_position=1
            )

    def test_main_page_position_can_have_multiple_nones(self):
        application1 = Application.objects.create(
            title="test application 1",
            notes="test description 1",
            main_page_position=None
        )
        assert application1.main_page_position is None

        application2 = Application.objects.create(
            title="test application 2",
            notes="test description 2",
            main_page_position=None
        )
        assert application2.main_page_position is None
