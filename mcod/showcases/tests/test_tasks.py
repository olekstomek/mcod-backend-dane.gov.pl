import os

from django.conf import settings
from django.test import override_settings

from mcod.showcases.models import ShowcaseProposal


class TestApplicationsTasks(object):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend',
                       EMAIL_FILE_PATH='/tmp/app-messages')
    def test_sending_application_proposal(self, datasets):
        image_b64 = [
            "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAElBMVEUAAAAAAACAgAC9vb3AwAD/",
            "/8AMUnRBAAAAAXRSTlMAQObYZgAAAEhJREFUeNqlzoEJwCAMRFETzv1XbvLlboEGmvIfIh6matd8",
            "zntrFuxsvf802S09OrUJQByBnAu+QzJAUoDRL1DAb4eSJqcp+QEhaQInIRvk4QAAAABJRU5ErkJg",
            "gg=="
        ]
        data = dict(
            category='app',
            license_type='free',
            title='Jakaś innowacja',
            notes='Nieszczególnie\nciekawy\nopis\ninnowacji',
            applicant_email='anyone@anywhere.any',
            author='Jan Kowalski',
            url='http://www.anywhere.any',
            datasets=[ds.id for ds in datasets[:2]],
            image=''.join(image_b64)
        )
        obj = ShowcaseProposal.create(data)
        assert obj.is_app
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

            for key in ('title', 'applicant_email', 'url', 'author'):
                assert data[key] in plain
                assert data[key] in html
            for ds in datasets[:2]:
                assert ds.frontend_absolute_url in plain
                assert ds.frontend_absolute_url in html

            assert data['notes'] in plain
            assert data['notes'].replace('\n', '<br>') in html
