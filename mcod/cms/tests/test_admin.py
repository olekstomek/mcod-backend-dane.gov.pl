from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.urls import reverse
from django.utils.encoding import force_str

from mcod.lib.utils import package_version_is_lower_than

client = Client()
User = get_user_model()


@override_settings(ROOT_URLCONF="mcod.cms.tests.cms_url_patterns")
def test_cms_login_redirects_to_admin_when_next_is_provided(admin):
    admin.set_password("secret123")
    admin.save()
    response = client.post(
        reverse("wagtailadmin_login"),
        data={
            "username": admin.email,
            "password": "secret123",
            "next": "/admin/",
        },
        follow=False,
    )
    assert response.status_code == 302

    if package_version_is_lower_than("django", 3, 2):
        assert response["Location"] == "/admin/"
    else:
        # https://docs.djangoproject.com/en/3.2/releases/3.2/
        raise Exception("changed it to: response.headers['Location']")


@override_settings(ROOT_URLCONF="mcod.cms.tests.cms_url_patterns")
def test_cms_login_axes_block(admin: User):
    payloads = {
        "username": admin.email,
        "password": "wrong password",
        "this_is_the_login_form": "1",
    }
    for _ in range(settings.AXES_FAILURE_LIMIT):
        client.post(reverse("wagtailadmin_login"), data=payloads)
    assert force_str(settings.AXES_FAIL_MESSAGE) in client.session["axes_lockout_message"]
