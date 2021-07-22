from django import forms
from mcod.lib.widgets import CKEditorWidget
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from mcod.lib.forms.fields import PhoneNumberField, InternalPhoneNumberField
from mcod.organizations.models import Organization
from mcod.core.db.models import STATUS_CHOICES
from localflavor.pl.forms import PLPostalCodeField, PLREGONField
from mcod.users.models import User


class OrganizationForm(forms.ModelForm):
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
        required=False
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
    website = forms.URLField(label=_("Website"))

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
        super(OrganizationForm, self).__init__(*args, **kwargs)
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
        super(OrganizationForm, self).save(commit=False)
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
