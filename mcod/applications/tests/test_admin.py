from django.test import Client
from django.urls import reverse
from pytest_bdd import scenarios

from mcod.applications.models import Application


scenarios(
    'features/application_details_admin.feature',
    'features/applications_list_admin.feature',
)


def test_save_model_given_created_by(admin, another_admin):
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
    client.force_login(admin)
    response = client.post(reverse('admin:applications_application_add'), obj, follow=True)
    assert response.status_code == 200
    ap1 = Application.objects.last()
    assert ap1.created_by.id == admin.id

    # add 2 application
    client = Client()
    client.force_login(another_admin)
    response = client.post(reverse('admin:applications_application_add'), obj2, follow=True)
    assert response.status_code == 200
    ap2 = Application.objects.last()
    assert ap2.created_by.id == another_admin.id
    assert ap1.id != ap2.id

    # change 1 application
    client = Client()
    client.force_login(another_admin)
    response = client.post(reverse('admin:applications_application_change', args=[ap1.id]), obj3, follow=True)
    assert response.status_code == 200

    # creator of app2 should be still admin
    assert Application.objects.get(id=ap1.id).created_by.id == admin.id


def test_add_tags_to_applications(admin, tag, tag_pl, application):
    data = {
        'title': "Test with dataset title",
        'slug': 'name',
        'notes': 'tresc',
        'url': "http://test.pl",
        'status': 'published',
        'tags_pl': [tag_pl.id],
    }

    assert tag_pl not in application.tags.all()
    client = Client()
    client.force_login(admin)
    client.post(reverse('admin:applications_application_change', args=[application.id]), data, follow=True)
    app = Application.objects.get(id=application.id)
    assert app.slug == "name"
    assert tag_pl in application.tags.all()
