from django import forms
from django.db.models import BLANK_CHOICE_DASH


class ExtendedSelect(forms.Select):
    def create_option(self, *args, **kwargs):
        result = super().create_option(*args, **kwargs)
        if [(result['value'], result['label'])] == BLANK_CHOICE_DASH:
            result['attrs']['aria-label'] = 'brak'
        return result
