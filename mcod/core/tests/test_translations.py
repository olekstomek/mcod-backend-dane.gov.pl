import pytest
from django.utils.translation import override
from pytest_bdd import scenarios

from mcod.settings.base import AXES_FAIL_MESSAGE

scenarios("features/translations.feature")


class TestSettings:
    @pytest.mark.django_db
    def test_axes_fail_message_is_translated_to_polish(self):
        with override("pl"):
            assert str(AXES_FAIL_MESSAGE) == "Zbyt wiele nieudanych prób logowania. Spróbuj ponownie później."

    def test_axes_fail_message_is_translated_to_english(self):
        with override("en"):
            assert str(AXES_FAIL_MESSAGE) == "Too many failed login attempts. Please try again later."
