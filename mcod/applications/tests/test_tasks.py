import pytest
import os

from mcod import settings
from mcod.applications.tasks import send_application_proposal


@pytest.mark.django_db
class TestApplicationsTaks(object):
    def test_sending_application_proposal(self, dataset_list):
        image_b64 = [
            "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAElBMVEUAAAAAAACAgAC9vb3AwAD/",
            "/8AMUnRBAAAAAXRSTlMAQObYZgAAAEhJREFUeNqlzoEJwCAMRFETzv1XbvLlboEGmvIfIh6matd8",
            "zntrFuxsvf802S09OrUJQByBnAu+QzJAUoDRL1DAb4eSJqcp+QEhaQInIRvk4QAAAABJRU5ErkJg",
            "gg=="
        ]
        app_proposal = dict(
            title="Jakaś aplikacja",
            notes="Nieszczególnie\nciekawy\nopis\naplikacji",
            applicant_email="anyone@anywhere.any",
            url="http://www.anywhere.any",
            datasets=[ds.id for ds in dataset_list[:2]],
            image=''.join(image_b64)
        )
        status = send_application_proposal(app_proposal)

        mail_filename = sorted(os.listdir(settings.EMAIL_FILE_PATH))[-1]
        last_mail_path = f"{settings.EMAIL_FILE_PATH}/{mail_filename}"
        with open(last_mail_path, 'r') as mail_file:
            mail = mail_file.read()

            plain_begin = mail.find('Content-Type: text/plain; charset="utf-8"\nMIME-Version: 1.0\n'
                                    'Content-Transfer-Encoding: 8bit')
            html_begin = mail.find('Content-Type: text/html; charset="utf-8"\nMIME-Version: 1.0\n'
                                   'Content-Transfer-Encoding: 8bit')
            image_begin = mail.find('Content-Type: image/png\nMIME-Version: 1.0\n'
                                    'Content-Transfer-Encoding: base64')

            plain = mail[plain_begin:html_begin]
            html = mail[html_begin:image_begin]
            image = mail[image_begin:]

            for key in ('title', 'applicant_email', 'url'):
                assert app_proposal[key] in plain
                assert app_proposal[key] in html

            for ds in dataset_list[:2]:
                ds_api_url = f"{settings.BASE_URL}/dataset/{ds.id}"
                assert ds_api_url in plain
                assert ds_api_url in html

            assert app_proposal['notes'] in plain
            _prepared = app_proposal['notes'].replace('\n', '<br>')

            assert _prepared in html

            i = image.find(image_b64[0])
            assert i > 0
            for line in image_b64[1:]:
                j = image.find(line)
                assert j == i + 77
                i = j
        assert status
