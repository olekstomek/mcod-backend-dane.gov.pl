import pytest
import re
from django.test import Client
from django.conf import settings


@pytest.mark.django_db
class TestCommonAdmin(object):
    def test_manual_link(self, admin_user):
        client = Client()
        client.force_login(admin_user)
        response = client.get('/', follow=True, HTTP_ACCEPT_LANGUAGE='pl')
        assert response.status_code == 200

        pattern = re.compile(f"<a href=['\"]"
                             f"{settings.CONSTANCE_CONFIG['MANUAL_URL'][0]}"
                             f"['\"] target=['\"]_blank['\"] class=['\"]icon['\"]>")
        assert len(pattern.findall(response.content.decode('utf-8'))) > 0
