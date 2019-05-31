import pytest
from django.db.models.query import QuerySet
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import Client
from django.conf import settings
from datetime import date
from mcod.applications.models import Application


@pytest.mark.django_db
class TestApplicationModel(object):
    def test_can_not_create_empty_application(self):
        with pytest.raises(ValidationError)as e:
            a = Application()
            a.full_clean()
        # assert "'slug'" in str(e.value)
        assert "'title'" in str(e.value)
        assert "'url'" in str(e.value)
        assert "'notes'" in str(e.value)
        # assert "'status'" in str(e.value)

    def test_create_application(self):
        a = Application()
        a.slug = "test-name"
        a.title = "Test name"
        a.notes = "Treść"
        a.url = "http://smth.smwheere.com"
        # a.status = 'active'
        assert a.full_clean() is None
        assert a.id is None
        a.save()
        assert a.id is not None
        assert a.status == "published"

    def test_add_dataset(self, valid_application, valid_dataset):
        valid_application.datasets.set([valid_dataset])
        assert valid_application.full_clean() is None
        valid_application.save()
        app = Application.objects.get(id=valid_application.id)
        assert valid_dataset in app.datasets.all()

    def test_add_dataset_twice(self, valid_application, valid_dataset):
        valid_application.datasets.set([valid_dataset])
        assert valid_application.full_clean() is None
        valid_application.save()
        app = Application.objects.get(id=valid_application.id)
        assert valid_dataset in app.datasets.all()
        assert len(app.datasets.all()) == 1
        valid_application.datasets.add(valid_dataset)
        assert valid_application.full_clean() is None
        valid_application.save()
        assert valid_dataset in app.datasets.all()
        assert len(app.datasets.all()) == 1

    def test_add_tag(self, valid_application, valid_tag):
        valid_application.tags.set([valid_tag])
        assert valid_application.full_clean() is None
        valid_application.save()
        app = Application.objects.get(id=valid_application.id)
        assert valid_tag in app.tags.all()

    def test_application_has_proper_columns_and_relations(self, valid_application):
        app_dict = valid_application.__dict__
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
        assert isinstance(valid_application.datasets.all(), QuerySet)
        assert isinstance(valid_application.tags.all(), QuerySet)

    def test_safe_delete(self, valid_application):
        assert valid_application.status == 'published'
        valid_application.delete()
        assert valid_application.is_removed is True
        with pytest.raises(ObjectDoesNotExist) as e:
            Application.objects.get(id=valid_application.id)
        assert "Application matching query does not exist." in str(e.value)
        assert Application.raw.get(id=valid_application.id)

    def test_unsafe_delete(self, valid_application):
        assert valid_application.status == 'published'
        valid_application.delete(soft=False)
        # assert valid_application.status == 'deleted'
        with pytest.raises(ObjectDoesNotExist) as e:
            Application.objects.get(id=valid_application.id)
        assert "Application matching query does not exist." in str(e.value)

    def test_image_path_and_url(self, valid_application, small_image):
        assert not valid_application.image
        valid_application.image = small_image
        valid_application.save()
        valid_application.refresh_from_db()
        assert valid_application.image
        assert valid_application.image_thumb
        date_folder = date.today().isoformat().replace('-', '')
        image_name = valid_application.image.name
        assert valid_application.image.url == f"/media/images/applications/{image_name}"
        assert valid_application.image.path == f"{settings.IMAGES_MEDIA_ROOT}/applications/{image_name}"
        assert date_folder in valid_application.image.url
        assert date_folder in valid_application.image.path


@pytest.mark.django_db
class TestApplicationUserRoles(object):
    def test_editor_doesnt_see_applications_in_admin_panel(self, editor_user):
        client = Client()
        client.login(email=editor_user.email, password="Britenet.1")
        response = client.get("/")
        assert response.status_code == 200
        assert '/applications/' not in str(response.content)

    def test_editor_cant_go_to_applications_in_admin_panel(self, editor_user):
        client = Client()
        client.login(email=editor_user.email, password="Britenet.1")
        response = client.get("/applications/")
        assert response.status_code == 404

    def test_admin_see_applications_in_admin_panel(self, admin_user):
        client = Client()
        client.login(email=admin_user.email, password="Britenet.1")
        response = client.get("/")
        assert response.status_code == 200
        assert '/applications/' in str(response.content)

    def test_admin_can_go_to_applications_in_admin_panel(self, admin_user):
        client = Client()
        client.login(email=admin_user.email, password="Britenet.1")
        response = client.get("/applications/")
        assert response.status_code == 200
