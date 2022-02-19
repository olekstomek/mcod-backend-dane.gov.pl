from mcod.datasets.widgets import CheckboxInputWithLabel
from mcod.lib.field_validators import ContainsLetterValidator
from mcod.lib.widgets import CKEditorWidget
from django import forms
from django.contrib.postgres.forms.jsonb import JSONField
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from mcod import settings
from mcod.core.db.models import STATUS_CHOICES
from mcod.datasets.field_validators import validate_dataset_image_file_extension
from mcod.datasets.models import UPDATE_FREQUENCY, Dataset
from mcod.lib.widgets import CheckboxSelect, JsonPairDatasetInputs
from mcod.tags.forms import ModelFormWithKeywords
from mcod.unleash import is_enabled


class DatasetForm(ModelFormWithKeywords):
    title = forms.CharField(
        widget=forms.Textarea(
            attrs={'placeholder': _('e.g. the name of the data set'),
                   'style': 'width: 99%', 'rows': 2}),
        label=_("Title"),
        max_length=300,
    )
    slug = forms.SlugField(label="Slug", widget=forms.TextInput(attrs={'size': 85}), required=False)
    notes = forms.CharField(
        min_length=20,
        widget=CKEditorWidget(
            attrs={
                'placeholder': _("Some information about the data being added"),
                'cols': 80,
                'rows': 10
            }
        ),
        required=True,
        label=_('Notes'),
        validators=[ContainsLetterValidator()],
    )
    notes_en = forms.CharField(
        min_length=20,
        widget=CKEditorWidget(
            attrs={
                'placeholder': _("Some information about the data being added"),
                'cols': 80,
                'rows': 10
            }
        ),
        required=False,
        label=_('Notes') + " (EN)",
        validators=[ContainsLetterValidator()],
    )
    update_frequency = forms.ChoiceField(
        choices=UPDATE_FREQUENCY,
        label=_("Update frequency")
    )
    url = forms.URLField(required=False,
                         widget=forms.TextInput(
                             attrs={
                                 'size': 85
                             }
                         ),
                         label=_("Source"),
                         max_length=1000
                         )

    customfields = JSONField(label=_("Customfields"),
                             widget=JsonPairDatasetInputs(
                                 val_attrs={'size': 35},
                                 key_attrs={'class': 'large'}
    ),
        required=False)

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        help_text=_(
            "If you select a draft, the status of all published resources belonging "
            "to that set will be changed to a draft"
        )
    )
    if is_enabled('S43_dynamic_data.be'):
        has_dynamic_data = forms.ChoiceField(
            required=True,
            label=_('dynamic data').capitalize(),
            choices=[(True, _('Yes')), (False, _('No'))],
            help_text=(
                'Zaznaczenie TAK spowoduje oznaczenie wszystkich nowo dodanych danych w zbiorze jako dane dynamiczne.'
                '<br><br>Jeżeli chcesz się więcej dowiedzieć na temat danych dynamicznych '
                '<a href="%(url)s" target="_blank">przejdź do strony</a>') % {
                'url': f'{settings.BASE_URL}{settings.DYNAMIC_DATA_MANUAL_URL}'},
            widget=CheckboxSelect(attrs={'class': 'inline'}),
        )
    if is_enabled('S41_resource_has_high_value_data.be'):
        has_high_value_data = forms.ChoiceField(
            required=True,
            label=_('has high value data').capitalize(),
            choices=[(True, _('Yes')), (False, _('No'))],
            help_text=(
                'Zaznaczenie TAK spowoduje oznaczenie wszystkich nowo dodanych danych w zbiorze jako dane o wysokiej '
                'wartości.<br><br>Jeżeli chcesz się więcej dowiedzieć na temat danych wysokiej wartości '
                '<a href="%(url)s" target="_blank">przejdź do strony</a>') % {
                'url': f'{settings.BASE_URL}{settings.HIGH_VALUE_DATA_MANUAL_URL}'},
            widget=CheckboxSelect(attrs={'class': 'inline'}),
        )

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        if 'categories' in self.fields and is_enabled('S41_dataset_categories_required.be'):
            self.fields['categories'].required = True
        try:
            self.fields['image'].validators.append(validate_dataset_image_file_extension)
            self.fields['image'].help_text = \
                _('Allowed file extensions: jpg, gif, png. For better readability,'
                  ' we recommend .png files with a transparent background')
        except KeyError:
            pass

        if self.fields.get('tags_pl'):
            self.fields['tags_pl'].required = True

        if 'update_notification_recipient_email' in self.fields:
            self.fields['update_notification_recipient_email'].required = True
            if instance and instance.modified_by and not instance.update_notification_recipient_email:
                self.initial['update_notification_recipient_email'] = instance.modified_by.email

    class Meta:
        model = Dataset
        widgets = {
            'license_condition_source': CheckboxInputWithLabel(label='CC BY 4.0'),
            'license_condition_modification': CheckboxInputWithLabel(label='CC BY 4.0'),
            'license_condition_responsibilities': CKEditorWidget(config_name='licenses'),
            'license_condition_db_or_copyrighted': CKEditorWidget(config_name='licenses'),
            'license_chosen': forms.RadioSelect,
            'license_condition_personal_data': CKEditorWidget(config_name='licenses'),
            'update_notification_frequency': forms.TextInput(attrs={'maxlength': 3}),
        }
        fields = [
            'title',
            'slug',
            'category',
            'categories',
            'notes',
            'tags',
            'organization',
            'url',
            'image',
            'update_frequency',
            'customfields',
            'license_condition_source',
            'license_condition_modification',
            'license_condition_responsibilities',
            'license_condition_db_or_copyrighted',
            'license_chosen',
            'license_condition_personal_data',
            'status',
        ]
        help_texts = {
            'update_notification_recipient_email': (
                'Uwaga! Adres email zostanie nadpisany adresem edytora, który będzie modyfikował metadane zbioru.'),
        }
        labels = {
            'created': _("Availability date"),
            'modified': _("Modification date"),
            'verified': _("Update date"),
            'archived_resources_files_media_url': _('Archived resources files')
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('license_condition_db_or_copyrighted') and not cleaned_data.get('license_chosen'):
            self.add_error('license_chosen', _('Text area is filled, license must be selected'))
        return cleaned_data

    def clean_license_condition_personal_data(self):
        if self.cleaned_data.get('license_condition_personal_data'):
            raise forms.ValidationError(_('Chosen conditions for re-use mean that they contain personal data. '
                                          'Please contact the administrator at kontakt@dane.gov.pl.'))
        return self.cleaned_data['license_condition_personal_data']

    def clean_status(self):
        if self.instance.id:
            organization = self.instance.organization
        else:
            organization = self.cleaned_data.get('organization')

        if organization and organization.status == 'draft':
            if self.cleaned_data['status'] == 'published':
                error_message = _(
                    "You can't publish this dataset, because his organization has the status of a draft "
                    "Please set status to draft or set status to publish for organization: "
                )

                error_message += "<a href='{}'>{}</a>".format(
                    reverse('admin:organizations_organization_change', args=[organization.id]),
                    organization.title
                )

                raise forms.ValidationError(mark_safe(error_message))

        return self.cleaned_data['status']


class DatasetStackedNoSaveForm(forms.ModelForm):
    title = forms.HiddenInput(attrs={'required': False})
    slug = forms.HiddenInput(attrs={'required': False})

    def save(self, commit=True):
        return super().save(commit=False)


class TrashDatasetForm(forms.ModelForm):

    def clean_is_removed(self):
        organization = self.instance.organization

        if self.cleaned_data['is_removed'] is False and organization.is_removed:
            error_message = _(
                "You can't restore this dataset, because it's organization is still removed. "
                "Please first restore organization: "
            )

            error_message += "<a href='{}'>{}</a>".format(
                reverse('admin:organizations_organizationtrash_change', args=[organization.id]),
                organization.title
            )

            raise forms.ValidationError(mark_safe(error_message))

        return self.cleaned_data['is_removed']
