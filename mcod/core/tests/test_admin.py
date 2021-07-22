import re
from django.test import Client
from django.conf import settings


class TestCommonAdmin(object):
    def test_manual_link(self, admin):
        client = Client()
        client.force_login(admin)
        response = client.get('/', follow=True, HTTP_ACCEPT_LANGUAGE='pl')
        assert response.status_code == 200

        pattern = re.compile(f"<a href=['\"]"
                             f"{settings.CONSTANCE_CONFIG['MANUAL_URL'][0]}"
                             f"['\"] target=['\"]_blank['\"] class=['\"]icon['\"]>")
        assert len(pattern.findall(response.content.decode('utf-8'))) > 0
