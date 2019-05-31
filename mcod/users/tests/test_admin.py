import pytest
from django.test import Client
from django.urls import reverse

from mcod.datasets.models import User


@pytest.mark.django_db
class TestUserAdmin:
    def test_superuser_get_queryset(self, admin_user, editor_user):
        client = Client()
        client.force_login(admin_user)
        response = client.get(reverse("admin:users_user_changelist"))
        assert response.content.count(b'field-email') == 2

    def test_editor_with_organization_get_queryset(self, admin_user, user_with_organization):
        client = Client()
        client.force_login(user_with_organization)
        response = client.get(reverse("admin:users_user_changelist"))
        assert response.content.count(b'field-email') == 1

    def test_editor_without_organization_get_queryset(self, admin_user, editor_user):
        client = Client()
        client.force_login(editor_user)
        response = client.get(reverse("admin:users_user_changelist"))
        assert response.content.count(b'field-email') == 1

    def test_editor_cant_see_is_staff_is_superuser_state_fields_in_form(self, editor_user):
        client = Client()
        client.force_login(editor_user)
        response = client.get(reverse("admin:users_user_change", args=(editor_user.id,)))
        assert 200 == response.status_code
        assert 'id_email' in str(response.content)
        assert 'id_is_staff' not in str(response.content)
        assert 'id_is_superuser' not in str(response.content)
        assert 'id_state' not in str(response.content)

    def test_editor_cant_change_himself_to_be_a_superuser_with_post_method(self, editor_user):
        client = Client()
        client.force_login(editor_user)
        response = client.post(
            reverse("admin:users_user_change", args=(editor_user.id,)),
            data={
                'email': editor_user.email,
                'fullname': editor_user.fullname,
                'phone': editor_user.phone,
                "is_superuser": True
            },
            follow=True
        )
        assert 200 == response.status_code
        assert 'To pole jest wymagane.' not in str(response.content)
        u = User.objects.get(id=editor_user.id)
        assert not u.is_superuser

    def test_admin_can_change_user_to_be_a_superuser_with_post_method(self, editor_user, admin_user):
        client = Client()
        client.force_login(admin_user)
        response = client.post(
            reverse("admin:users_user_change", args=(editor_user.id,)),
            data={
                'email': editor_user.email,
                "is_superuser": True,
                'state': 'active'
            },
            follow=True
        )
        assert 200 == response.status_code
        u = User.objects.get(id=editor_user.id)
        assert u.email == editor_user.email
        assert u.is_superuser

    def test_login_email_is_case_insensitive(self, editor_user):
        client = Client()
        payloads = {
            'email': editor_user.email.upper(),
            'password': "Britenet.1"
        }
        client.login(**payloads)
        response = client.get(reverse("admin:users_user_changelist"))
        assert 200 == response.status_code
