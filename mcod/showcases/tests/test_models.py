from datetime import date

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models.query import QuerySet
from django.test import Client
from django.utils.encoding import smart_str

from mcod.showcases.models import Showcase


class TestShowcaseModel(object):
    def test_can_not_create_empty_showcase(self):
        with pytest.raises(ValidationError)as e:
            a = Showcase()
            a.full_clean()
        assert "'title'" in str(e.value)
        assert "'url'" in str(e.value)
        assert "'notes'" in str(e.value)

    def test_create_application(self):
        a = Showcase()
        a.category = 'app'
        a.license_type = 'free'
        a.slug = 'test-name'
        a.title = 'Test name'
        a.notes = 'Treść'
        a.url = 'http://smth.smwheere.com'
        assert a.full_clean() is None
        assert a.id is None
        a.save()
        assert a.id is not None
        assert a.status == 'published'

    def test_add_dataset(self, showcase, dataset):
        showcase.datasets.set([dataset])
        assert showcase.full_clean() is None
        showcase.save()
        obj = Showcase.objects.get(id=showcase.id)
        assert dataset in obj.datasets.all()

    def test_add_tag(self, showcase, tag):
        showcase.tags.set([tag])
        assert showcase.full_clean() is None
        showcase.save()
        app = Showcase.objects.get(id=showcase.id)
        assert tag in app.tags.all()

    def test_showcase_has_proper_columns_and_relations(self, showcase):
        obj_dict = showcase.__dict__
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
            assert f in obj_dict
        assert isinstance(showcase.datasets.all(), QuerySet)
        assert isinstance(showcase.tags.all(), QuerySet)

    def test_safe_delete(self, showcase):
        assert showcase.status == 'published'
        showcase.delete()
        assert showcase.is_removed is True
        with pytest.raises(ObjectDoesNotExist) as e:
            Showcase.objects.get(id=showcase.id)
        assert "Showcase matching query does not exist." in str(e.value)
        assert Showcase.raw.get(id=showcase.id)

    def test_unsafe_delete(self, showcase):
        assert showcase.status == 'published'
        showcase.delete(soft=False)
        with pytest.raises(ObjectDoesNotExist) as e:
            Showcase.objects.get(id=showcase.id)
        assert "Showcase matching query does not exist." in str(e.value)

    def test_image_path_and_url(self, showcase, small_image):
        showcase.image = small_image
        showcase.save()
        showcase.refresh_from_db()
        assert showcase.image
        assert showcase.image_thumb
        date_folder = date.today().isoformat().replace('-', '')
        image_name = showcase.image.name
        assert showcase.image.url == f'/media/showcases/{image_name}'
        assert showcase.image.path == f'{settings.SHOWCASES_MEDIA_ROOT}/{image_name}'
        assert date_folder in showcase.image.url
        assert date_folder in showcase.image.path

    def test_main_page_position_on_create(self):
        showcase1 = Showcase.objects.create(title="test showcase 1", notes="test description 1")
        assert showcase1.main_page_position is None, "main page position should be None if not specified"

    def test_main_page_position_no_duplicates(self):
        showcase1 = Showcase.objects.create(
            title="test showcase 1",
            notes="test description 1",
            main_page_position=1
        )
        assert showcase1.main_page_position == 1

        with pytest.raises(IntegrityError):
            Showcase.objects.create(
                title="test showcase 2",
                notes="test description 2",
                main_page_position=1
            )

    def test_main_page_position_can_have_multiple_nones(self):
        showcase1 = Showcase.objects.create(
            title="test showcase 1",
            notes="test description 1",
            main_page_position=None
        )
        assert showcase1.main_page_position is None

        showcase2 = Showcase.objects.create(
            title="test showcase 2",
            notes="test description 2",
            main_page_position=None
        )
        assert showcase2.main_page_position is None


class TestShowcaseUserRoles(object):
    def test_editor_doesnt_see_showcases_in_admin_panel(self, active_editor):
        client = Client()
        client.login(email=active_editor.email, password='12345.Abcde')
        response = client.get('/')
        assert response.status_code == 200
        assert '/showcases/' not in smart_str(response.content)

    def test_editor_cant_go_to_showcases_in_admin_panel(self, active_editor):
        client = Client()
        client.login(email=active_editor.email, password='12345.Abcde')
        response = client.get('/showcases/')
        assert response.status_code == 404

    def test_admin_see_showcases_in_admin_panel(self, admin):
        client = Client()
        client.login(email=admin.email, password='12345.Abcde')
        response = client.get('/')
        assert response.status_code == 200
        assert '/showcases/' in smart_str(response.content)

    def test_admin_can_go_to_showcases_in_admin_panel(self, admin):
        client = Client()
        client.login(email=admin.email, password='12345.Abcde')
        response = client.get('/showcases/')
        assert response.status_code == 200
