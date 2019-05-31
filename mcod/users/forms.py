from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import forms as auth_forms
from django.utils.translation import gettext_lazy as _
from mcod.users.models import User
from mcod.organizations.models import Organization
from mcod.lib.forms.fields import PhoneNumberField, InternalPhoneNumberField


class UserForm(forms.ModelForm):
    organizations = forms.ModelMultipleChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(_('organizations'), False),
        label=_("Organizations")
    )
    phone = PhoneNumberField(label=_("Phone number"), required=False)
    phone_internal = InternalPhoneNumberField(label=_("int."), required=False)

    def clean_phone_internal(self):
        if self.cleaned_data['phone_internal'] and not self.cleaned_data.get('phone'):
            raise InternalPhoneNumberField.NoMainNumberError
        return self.cleaned_data['phone_internal']

    def save(self, commit=True):
        super(UserForm, self).save(commit=False)
        if commit:
            self.instance.save()
        if self.instance.pk:
            self.instance.organizations.set(self.cleaned_data['organizations'])
        return self.instance


class UserCreationForm(UserForm):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = User
        fields = ['email', 'fullname', 'phone', 'phone_internal', 'is_staff', 'is_superuser', 'state',
                  'organizations']

    def clean_email(self):
        email = self.data.get('email', "")
        if email and User.objects.filter(email__iexact=email).exists():
            self.add_error('email', _('Account for this email already exist'))
        return self.data.get('email', "").lower()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        super(UserCreationForm, self).save(commit=False)
        self.instance.set_password(self.cleaned_data["password1"])
        if commit:
            self.instance.save()
        if self.instance.pk:
            self.instance.organizations.set(self.cleaned_data['organizations'])
        return self.instance


class UserChangeForm(UserForm):
    password = auth_forms.ReadOnlyPasswordHashField(label=_("Password"),
                                                    help_text=_(
                                                        "Raw passwords are not stored, so there is no way to see "
                                                        "this user's password, but you can change the password "
                                                        "using <a href=\"../password/\">this form</a>."))

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')
        if self.instance.pk:
            self.fields['organizations'].initial = self.instance.organizations.all()

    def clean_password(self):
        return self.initial["password"]
