from mcod.datasets.widgets import CheckboxInputWithLabel
from mcod.lib.widgets import CKEditorWidget
from django import forms
from django.contrib.postgres.forms.jsonb import JSONField
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from mcod.core.db.models import STATUS_CHOICES
from mcod.datasets.field_validators import validate_dataset_image_file_extension
from mcod.datasets.models import UPDATE_FREQUENCY, Dataset
from mcod.lib.widgets import JsonPairDatasetInputs
from mcod.lib.dcat.vocabularies.metaclasses import DcatVocabAdminFormMetaClass
from mcod.tags.forms import ModelFormWithKeywords
from mcod.unleash import is_enabled


class DatasetForm(ModelFormWithKeywords, metaclass=DcatVocabAdminFormMetaClass):
    title = forms.CharField(
        widget=forms.Textarea(
            attrs={'placeholder': _('e.g. the name of the data set'),
                   'style': 'width: 99%', 'rows': 1}),
        label=_("Title"),
        max_length=300,
    )
    slug = forms.SlugField(label="Slug", widget=forms.TextInput(attrs={'size': 85}), required=False)
    notes = forms.CharField(
        widget=CKEditorWidget(
            attrs={
                'placeholder': _("Some information about the data being added"),
                'cols': 80,
                'rows': 10
            }
        ),
        required=True,
        label=_('Notes')
    )
    notes_en = forms.CharField(
        widget=CKEditorWidget(
            attrs={
                'placeholder': _("Some information about the data being added"),
                'cols': 80,
                'rows': 10
            }
        ),
        required=False,
        label=_('Notes') + " (EN)"
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

    if not is_enabled('S21_licenses.be'):
        license_condition_source = forms.BooleanField(
            label=_(
                "The recipient should inform about the date, "
                "time of completion and obtaining information from the obliged entity"
            ),
            required=False
        )

        license_condition_modification = forms.BooleanField(
            label=_("The recipient should inform about the processing of the information when it modifies it"),
            required=False
        )

        license_condition_responsibilities = forms.CharField(
            label=_("The scope of the provider's responsibility for the information provided"),
            widget=CKEditorWidget,
            required=False
        )

        license_condition_db_or_copyrighted = forms.CharField(
            label=_("Conditions for using public information that meets the characteristics of the work or constitute "
                    "a database (Article 13 paragraph 2 of the Act on the re-use of public sector information)"),
            widget=CKEditorWidget,
            required=False
        )

        license_condition_personal_data = forms.CharField(
            label=_("Conditions for using public sector information containing personal data (Article 14 paragraph 1 "
                    "point 4 of the Act on the re-use of public Sector Information)"),
            widget=CKEditorWidget,
            required=False
        )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        help_text=_(
            "If you select a draft, the status of all published resources belonging "
            "to that set will be changed to a draft"
        )
    )

    def __init__(self, *args, **kwargs):
        super(DatasetForm, self).__init__(*args, **kwargs)
        try:
            self.fields['image'].validators.append(validate_dataset_image_file_extension)
            self.fields['image'].help_text = \
                _('Allowed file extensions: jpg, gif, png. For better readability,'
                  ' we recommend .png files with a transparent background')
        except KeyError:
            pass

        try:
            self.fields['categories'].required = False
        except KeyError:
            pass
        if is_enabled('S21_admin_ui_changes.be') and self.fields.get('title'):
            self.fields['title'].widget.attrs['rows'] = 2

        if is_enabled('S18_new_tags.be') and self.fields.get('tags_pl'):
            self.fields['tags_pl'].required = True

    class Meta:
        model = Dataset
        if is_enabled('S21_licenses.be'):
            widgets = {
                'license_condition_source': CheckboxInputWithLabel(label='CC BY 4.0'),
                'license_condition_modification': CheckboxInputWithLabel(label='CC BY 4.0'),
                'license_condition_responsibilities': CKEditorWidget(config_name='licenses'),
                'license_condition_db_or_copyrighted': CKEditorWidget(config_name='licenses'),
                'license_chosen': forms.RadioSelect,
                'license_condition_personal_data': CKEditorWidget(config_name='licenses'),
            }

            license_fields = (
                "license_condition_source",
                "license_condition_modification",
                "license_condition_responsibilities",
                "license_condition_db_or_copyrighted",
                "license_chosen",
                "license_condition_personal_data",
            )
        else:
            license_fields = (
                'license_condition_db_or_copyrighted',
                'license_condition_personal_data',
                'license_condition_modification',
                'license_condition_responsibilities',
                'license_condition_source',
            )
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
            *license_fields,
            'status',
        ]
        labels = {
            'created': _("Availability date"),
            'modified': _("Modification date"),
            'verified': _("Update date"),
        }

    def clean(self):
        cleaned_data = super().clean()
        if is_enabled('S21_licenses.be'):
            if cleaned_data.get('license_condition_db_or_copyrighted') and not cleaned_data.get('license_chosen'):
                self.add_error('license_chosen', _('Text area is filled, license must be selected'))
        return cleaned_data

    def clean_license_condition_personal_data(self):
        if is_enabled('S21_licenses.be') and self.cleaned_data.get('license_condition_personal_data'):
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


class DatasetListForm(forms.ModelForm):
    title = forms.HiddenInput(attrs={'required': False})
    slug = forms.HiddenInput(attrs={'required': False})


class AddDatasetForm(DatasetForm):
    pass


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
