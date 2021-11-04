from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from django.core import mail
from django.test import override_settings

from mcod.datasets.tasks import send_dataset_update_reminder


class TestDatasetUpdateReminder:

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @pytest.mark.parametrize("update_freq, date_delay, reldelta", [
        ('weekly', 1, relativedelta(days=7)),
        ('monthly', 3, relativedelta(months=1)),
        ('quarterly', 7, relativedelta(months=3)),
        ('everyHalfYear', 7, relativedelta(months=6)),
        ('yearly', 7, relativedelta(years=1)),
    ])
    def test_update_reminder_is_sent(self, update_freq, date_delay, reldelta, dataset_with_resource, admin):
        ds = dataset_with_resource
        ds.title = 'Test wysyłki notyfikacji dot. aktualizacji zbioru'
        ds.update_frequency = update_freq
        ds.modified_by = admin
        ds.save()
        first_res = ds.resources.all()[0]
        first_res.data_date = date.today() + relativedelta(days=date_delay) - reldelta
        first_res.type = 'file'
        first_res.save()
        send_dataset_update_reminder()
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Test wysyłki notyfikacji dot. aktualizacji zbioru'
        assert 'Przypomnienie o aktualizacji Zbioru danych' in mail.outbox[0].body
        assert mail.outbox[0].to == [admin.email]

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @pytest.mark.parametrize("res_type, update_freq, date_delay, reldelta, notification_enabled", [
        ('api', 'weekly', 1, relativedelta(days=7), True),
        ('website', 'monthly', 3, relativedelta(months=1), True),
        ('file', 'monthly', 3, relativedelta(months=1), False),
        ('file', 'notApplicable', 3, relativedelta(months=1), True),
        ('file', 'daily', 3, relativedelta(months=1), True),
    ])
    def test_update_reminder_is_not_sent(self, res_type, update_freq, date_delay, reldelta, notification_enabled,
                                         dataset_with_resource, admin):
        ds = dataset_with_resource
        ds.update_frequency = update_freq
        ds.modified_by = admin
        ds.is_update_notification_enabled = notification_enabled
        ds.save()
        first_res = ds.resources.all()[0]
        first_res.data_date = date.today() + relativedelta(days=date_delay) - reldelta
        first_res.type = res_type
        first_res.save()
        send_dataset_update_reminder()
        assert len(mail.outbox) == 0

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_update_reminder_sent_to_notification_recipient_if_set(self, dataset_with_resource, admin):
        ds = dataset_with_resource
        ds.title = 'Test wysyłki notyfikacji dot. aktualizacji zbioru'
        ds.update_frequency = 'weekly'
        ds.modified_by = admin
        ds.update_notification_recipient_email = 'test-recipient@test.com'
        ds.save()
        first_res = ds.resources.all()[0]
        first_res.data_date = date.today() + relativedelta(days=1) - relativedelta(days=7)
        first_res.type = 'file'
        first_res.save()
        send_dataset_update_reminder()
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Test wysyłki notyfikacji dot. aktualizacji zbioru'
        assert mail.outbox[0].to == ['test-recipient@test.com']
        assert mail.outbox[0].to != [admin.email]
