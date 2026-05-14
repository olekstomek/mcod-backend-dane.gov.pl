from contextlib import suppress
from importlib import reload
from typing import Set, Tuple

import axes.admin
import pytest
from axes.models import AccessAttempt, AccessLog
from bs4 import BeautifulSoup
from django.conf import settings as django_settings
from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import NoReverseMatch, clear_url_caches, reverse
from django.utils.encoding import force_str, smart_str
from pytest_bdd import scenarios

import mcod.urls
from mcod.lib.utils import package_version_is_lower_than

scenarios("features/admin.feature")
scenarios("features/admin_forms.feature")
scenarios("features/meetings.feature")

User = get_user_model()
admin_login_url = reverse("admin:login")


class TestDjangoAxes:
    """Tests Django Axes integration in the admin panel.

    Covers Axes admin visibility, access permissions, and lockout behavior
    for different user roles and Axes configuration states.
    """

    @staticmethod
    def _set_axes_admin_state():
        """Rebuild Axes admin and URL state based on current settings.

        Clears any existing Axes admin registrations and reloads admin modules
        and URL configuration so they reflect the current setting.
        """
        with suppress(django_admin.sites.NotRegistered):
            django_admin.site.unregister(AccessAttempt)
        with suppress(django_admin.sites.NotRegistered):
            django_admin.site.unregister(AccessLog)

        reload(axes.admin)
        clear_url_caches()
        reload(mcod.urls)

    @staticmethod
    def _login_to_admin(client: Client, user, password: str):
        response = client.post(
            admin_login_url,
            data={
                "username": user.email,
                "password": password,
                "this_is_the_login_form": "1",
            },
        )
        assert response.status_code == 302

    @staticmethod
    def _get_admin_index_links(client: Client) -> Set[str]:
        response = client.get(reverse("admin:index"))
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        return {a.get("href") for a in soup.select("a[href]")}

    @staticmethod
    def _get_axes_urls() -> Tuple[str, str]:
        return (
            reverse("admin:axes_accessattempt_changelist"),
            reverse("admin:axes_accesslog_changelist"),
        )

    @pytest.fixture
    def with_axes_enabled(self, settings):
        settings.AXES_ENABLE_ADMIN = True
        self._set_axes_admin_state()
        yield
        self._set_axes_admin_state()

    @pytest.fixture
    def with_axes_disabled(self, settings):
        settings.AXES_ENABLE_ADMIN = False
        self._set_axes_admin_state()
        yield
        self._set_axes_admin_state()

    @pytest.mark.usefixtures("with_axes_enabled")
    @pytest.mark.parametrize(
        "user_fixture, should_see_axes",
        [
            ("admin", True),
            ("active_editor", False),
        ],
    )
    def test_axes_panel_visibility_when_enabled(self, request, user_fixture: str, should_see_axes: bool, test_password: str):
        user = request.getfixturevalue(user_fixture)
        client = Client()

        self._login_to_admin(client, user, test_password)
        links = self._get_admin_index_links(client)
        accessattempt_url, accesslog_url = self._get_axes_urls()

        assert (accessattempt_url in links) is should_see_axes
        assert (accesslog_url in links) is should_see_axes

    @pytest.mark.usefixtures("with_axes_disabled")
    @pytest.mark.parametrize(
        "user_fixture",
        [
            "admin",
            "active_editor",
        ],
    )
    def test_axes_panel_not_visible_when_disabled(self, request, user_fixture: str, test_password: str):
        client = Client()
        user = request.getfixturevalue(user_fixture)

        self._login_to_admin(client, user, test_password)

        links = self._get_admin_index_links(client)
        assert not any("/axes/accessattempt/" in (link or "") for link in links)
        assert not any("/axes/accesslog/" in (link or "") for link in links)

    def test_login_axes_block(self, admin):
        client = Client()
        payloads = {
            "username": admin.email,
            "password": "wrong password",
            "this_is_the_login_form": "1",
        }
        for _ in range(django_settings.AXES_FAILURE_LIMIT):
            client.post(admin_login_url, data=payloads)
        assert force_str(django_settings.AXES_FAIL_MESSAGE) in client.session["axes_lockout_message"]

    @pytest.mark.usefixtures("with_axes_enabled")
    @pytest.mark.parametrize(
        "user_fixture, status_code",
        [
            ("admin", 200),
            ("active_editor", 403),
        ],
    )
    def test_axes_urls_access_when_enabled(self, request, user_fixture: str, status_code: int, test_password: str):
        user = request.getfixturevalue(user_fixture)
        client = Client()

        self._login_to_admin(client, user, test_password)
        links = self._get_axes_urls()

        for link in links:
            response = client.get(link)
            assert response.status_code == status_code

    @pytest.mark.usefixtures("with_axes_disabled")
    def test_axes_urls_not_available_when_disabled(self):
        with pytest.raises(NoReverseMatch):
            reverse("admin:axes_accessattempt_changelist")
        with pytest.raises(NoReverseMatch):
            reverse("admin:axes_accesslog_changelist")


class TestUserAdmin:
    def test_superuser_get_queryset(self, admin):
        client = Client()
        client.force_login(admin)
        response = client.get(reverse("admin:users_user_changelist"))
        assert response.content.count(b"field-email") == 1

    def test_admin_form_fields_rendered(self, admin):
        """Test if "Logowanie przez WK" text is displayed in response content."""
        client = Client()
        client.force_login(admin)
        url = reverse("admin:users_user_change", args=[admin.id])
        response = client.get(url)
        assert "Logowanie przez WK" in response.content.decode()

    def test_editor_with_organization_get_queryset(self, admin, active_editor):
        client = Client()
        client.force_login(active_editor)
        response = client.get(reverse("admin:users_user_changelist"))
        assert response.content.count(b"field-email") == 1

    def test_editor_without_organization_get_queryset(self, admin, active_editor):
        client = Client()
        client.force_login(active_editor)
        response = client.get(reverse("admin:users_user_changelist"))
        assert response.content.count(b"field-email") == 1

    def test_editor_cant_see_is_staff_is_superuser_state_fields_in_form(self, active_editor):
        client = Client()
        client.force_login(active_editor)
        response = client.get(active_editor.admin_change_url)
        assert 200 == response.status_code
        assert "id_email" in smart_str(response.content)
        assert '"id_is_staff"' not in smart_str(response.content)
        assert "id_is_superuser" not in smart_str(response.content)
        assert "id_state" not in smart_str(response.content)

    def test_editor_cant_change_himself_to_be_a_superuser_with_post_method(self, active_editor):
        client = Client()
        client.force_login(active_editor)
        response = client.post(
            active_editor.admin_change_url,
            data={
                "email": active_editor.email,
                "fullname": active_editor.fullname,
                "phone": active_editor.phone,
                "is_superuser": True,
            },
            follow=True,
        )
        assert 200 == response.status_code
        assert "To pole jest wymagane." not in smart_str(response.content)
        u = User.objects.get(id=active_editor.id)
        assert not u.is_superuser

    def test_login_email_is_case_insensitive(self, active_editor: User, test_password: str):
        client = Client()
        payloads = {"username": active_editor.email.upper(), "password": test_password}
        client.post(admin_login_url, data=payloads)
        response = client.get(reverse("admin:users_user_changelist"))
        assert 200 == response.status_code

    def test_admin_login_redirects_to_admin_index_without_next(self, admin: User, test_password: str):
        client = Client()
        response = client.post(
            admin_login_url,
            data={
                "username": admin.email,
                "password": test_password,
                "this_is_the_login_form": "1",
            },
        )
        assert response.status_code == 302

        if package_version_is_lower_than("django", 3, 2):
            assert response["Location"] == reverse("admin:index")
        else:
            # https://docs.djangoproject.com/en/3.2/releases/3.2/   noqa: E265
            raise Exception("changed it to: response.headers['Location']")

    def test_admin_login_redirects_to_next_when_provided(self, admin: User, test_password: str):
        client = Client()
        next_url = reverse("admin:users_user_changelist")

        response = client.post(
            admin_login_url,
            data={
                "username": admin.email,
                "password": test_password,
                "this_is_the_login_form": "1",
                "next": next_url,
            },
        )

        assert response.status_code == 302

        if package_version_is_lower_than("django", 3, 2):
            assert response["Location"] == next_url
        else:
            # https://docs.djangoproject.com/en/3.2/releases/3.2/  noqa: E265
            raise Exception("changed it to: response.headers['Location']")

    def test_admin_can_set_user_as_academy_admin_and_labs_admin(self, active_editor, admin):
        assert active_editor.is_academy_admin is False
        assert active_editor.is_labs_admin is False
        client = Client()
        client.force_login(admin)
        response = client.post(
            active_editor.admin_change_url,
            data={
                "email": active_editor.email,
                "is_superuser": False,
                "state": "active",
                "is_academy_admin": True,
                "is_labs_admin": True,
            },
            follow=True,
        )
        assert 200 == response.status_code
        u = User.objects.get(id=active_editor.id)
        assert u.is_academy_admin
        assert u.is_labs_admin

    def test_editor_change_form_doesnt_unsets_organizations(self, active_editor):
        client = Client()
        client.force_login(active_editor)
        response = client.post(
            active_editor.admin_change_url,
            data={
                "email": "new_mail@test.com",
                "fullname": active_editor.fullname,
                "phone": "111111111",
            },
            follow=True,
        )
        u = User.objects.get(id=active_editor.id)
        assert 200 == response.status_code
        assert u.organizations.exists()

    @pytest.mark.parametrize(
        "weak_password", ["123", "abc", "Aa1Bb2Cc3", "abc123", "abcd1234", "abcdefgh", "12345678", "ABCD1234"]
    )
    def test_admin_cannot_create_user_with_weak_password(self, admin, weak_password: str):
        # GIVEN
        possible_error_messages = (
            "To hasło jest za krótkie. Musi zawierać co najmniej 8 znaków.",
            "Hasło musi zawierać przynajmniej jedną cyfrę.",
            "Hasło musi zawierać przynajmniej jedną dużą i jedną małą literę.",
            "Hasło musi zawierać przynajmniej jeden znak specjalny.",
            "To hasło jest zbyt powszechne.",
        )
        client = Client()
        client.force_login(admin)
        email = "non_existing_email@test.com"

        # WHEN admin tries to create a user with weak password in Admin Panel
        response = client.post(
            admin.get_admin_add_url(),
            data={
                "email": email,
                "fullname": "Best User",
                "phone": "111111111",
                "password1": weak_password,
                "password2": weak_password,
            },
        )

        # THEN
        # User with given name was not created
        user_exists: bool = User.objects.filter(email=email).exists()
        assert not user_exists

        # At least one of possible password related error messages was listed
        str_response_content: str = smart_str(response.content)
        assert any((err_msg in str_response_content for err_msg in possible_error_messages))
