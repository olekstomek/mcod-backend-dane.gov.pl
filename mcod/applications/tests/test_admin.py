import re

import pytest
from django.test import Client
from django.urls import reverse

from mcod.applications.models import Application


@pytest.mark.django_db
def test_save_model_auto_create_slug(admin_user):
    obj = {
        'title': "Test with application title",
        # 'slug': "test-with-application-title",
        'notes': "Tresc",
        'url': "http://test.pl",
        'status': 'published',
    }

    client = Client()
    client.force_login(admin_user)
    response = client.post(reverse('admin:applications_application_add'), obj, follow=True)
    assert response.status_code == 200
    assert "test-with-application-title" == Application.objects.last().slug


@pytest.mark.django_db
def test_save_model_manual_create_name(admin_user):
    obj = {
        'title': "Test with dataset title",
        'slug': 'manual-name',
        'notes': 'tresc',
        'status': 'published',
        'url': "http://test.pl", }

    client = Client()
    client.force_login(admin_user)
    response = client.post(reverse('admin:applications_application_add'), obj, follow=True)
    assert response.status_code == 200

    assert Application.objects.last().slug == "manual-name"


@pytest.mark.django_db
def test_save_model_given_created_by(admin_user, admin_user2):
    obj = {
        'title': "Test with dataset title 1",
        'slug': 'manual-name-1',
        'notes': 'tresc',
        'status': 'published',
        'url': "http://1.test.pl",
    }

    obj2 = {
        'title': "Test with dataset title 2",
        'slug': 'manual-name-2',
        'notes': 'tresc',
        'status': 'published',
        'url': "http://2.test.pl",
    }

    obj3 = {
        'title': "Test with dataset title 3",
        'slug': 'manual-name-1',
        'notes': 'tresc',
        'status': 'published',
        'url': "http://1.test.pl",
    }

    # add 1 application
    client = Client()
    client.force_login(admin_user)
    response = client.post(reverse('admin:applications_application_add'), obj, follow=True)
    assert response.status_code == 200
    ap1 = Application.objects.last()
    assert ap1.created_by.id == admin_user.id

    # add 2 application
    client = Client()
    client.force_login(admin_user2)
    response = client.post(reverse('admin:applications_application_add'), obj2, follow=True)
    assert response.status_code == 200
    ap2 = Application.objects.last()
    assert ap2.created_by.id == admin_user2.id
    assert ap1.id != ap2.id

    # change 1 application
    client = Client()
    client.force_login(admin_user2)
    response = client.post(reverse('admin:applications_application_change', args=[ap1.id]), obj3, follow=True)
    assert response.status_code == 200

    # creator of app2 should be still admin_user
    assert Application.objects.get(id=ap1.id).created_by.id == admin_user.id


@pytest.mark.django_db
def test_add_tags_to_applications(admin_user, valid_tag, valid_application):
    obj = {
        'title': "Test with dataset title",
        'slug': 'name',
        'notes': 'tresc',
        'url': "http://test.pl",
        'status': 'published',
        'tags': [valid_tag.id]

    }

    assert valid_application.slug == "test-name"
    assert valid_tag not in valid_application.tags.all()
    client = Client()
    client.force_login(admin_user)
    client.post(reverse('admin:applications_application_change', args=[valid_application.id]), obj, follow=True)
    app = Application.objects.get(id=valid_application.id)
    assert app.slug == "name"
    assert valid_tag in app.tags.all()


@pytest.mark.django_db
def test_removed_applications_are_not_in_applicaiton_list(admin_user, valid_application):
    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("admin:applications_application_changelist"))
    pattern = re.compile(r"/applications/application/\d+/change")
    result = pattern.findall(str(response.content))
    assert result == [f'/applications/application/{valid_application.id}/change']
    valid_application.delete()
    response = client.get(reverse("admin:applications_application_changelist"))
    result = pattern.findall(str(response.content))
    assert not result
