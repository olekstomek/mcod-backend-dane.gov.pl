from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _
from localflavor.pl.forms import PLPostalCodeField, PLREGONField

from mcod.core.db.models import STATUS_CHOICES
from mcod.lib.forms.fields import InternalPhoneNumberField, PhoneNumberField
from mcod.lib.widgets import CKEditorWidget
from mcod.organizations.models import Organization
from mcod.users.models import User
from mcod.unleash import is_enabled


class OrganizationForm(forms.ModelForm):
    title = forms.CharField(label=_('Name'), max_length=110)
    title_en = forms.CharField(label=_('Name') + ' (EN)', max_length=110, required=False, empty_value=None)
    description = forms.CharField(
        widget=CKEditorWidget(
            attrs={
                'placeholder': _("Some information about the institution"),
            }
        ),
        label=_("Description"),
        required=False
    )
    description_en = forms.CharField(
        widget=CKEditorWidget(
            attrs={
                'placeholder': _("Some information about the institution"),
            }
        ),
        label=_("Description") + " (EN)",
        required=False,
        empty_value=None,
    )
    tel = PhoneNumberField(label=_("Phone number"), required=True)
    fax = PhoneNumberField(label=_("Fax number"), required=False)
    tel_internal = InternalPhoneNumberField(label=_("int."), required=False)
    fax_internal = InternalPhoneNumberField(label=_("int."), required=False)
    slug = forms.SlugField(required=False)

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_staff=True),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_('Users'),
            is_stacked=False
        ),
        label=_("Users")

    )
    postal_code = PLPostalCodeField(label=_("Postal code"))
    regon = PLREGONField()
    website = (
        forms.URLField(label=_("Website"), required=False)
        if is_enabled("S58_fix_institution_website_not_required.be")
        else forms.URLField(label=_("Website"))
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        help_text=_(
            "If you select a draft, the status of all published datasets belonging "
            "to this institution will be changed to a draft."
            "Also all resources of those datasets will be change to a draft"
        )

    )

    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'abbreviation' in self.fields:
            self.fields['abbreviation'].required = False
        if 'epuap' in self.fields:
            self.fields['epuap'].required = False
        if self.instance.pk:
            self.fields['users'].initial = self.instance.users.all()

    def clean_fax_internal(self):
        if 'fax' not in self.cleaned_data:
            return
        if self.cleaned_data.get('fax_internal') and not self.cleaned_data.get('fax'):
            raise InternalPhoneNumberField.NoMainNumberError
        return self.cleaned_data.get('fax_internal')

    def clean_tel_internal(self):
        if self.cleaned_data.get('tel_internal') and not self.cleaned_data.get('tel'):
            raise InternalPhoneNumberField.NoMainNumberError
        return self.cleaned_data.get('tel_internal')

    def save(self, commit=True):
        super().save(commit=False)
        if commit:
            self.instance.save()
        if self.instance.pk:
            self.instance.users.set(self.cleaned_data['users'])
            self.save_m2m()
        return self.instance

    class Meta:
        model = Organization
        fields = [
            'slug',
            'title',
            'institution_type',
            'postal_code',
            'city',
            'street',
            'street_number',
            'flat_number',
            'street_type',
            'email',
            'fax',
            'tel',
            'epuap',
            'regon',
            'website',
            'users'
        ]
