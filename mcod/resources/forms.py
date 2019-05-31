from ckeditor.widgets import CKEditorWidget
from dateutil.utils import today
from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class ResourceSourceSwitcher(forms.widgets.HiddenInput):
    input_type = 'hidden'
    template_name = 'admin/forms/widgets/resources/switcher.html'


class ResourceSwitcherField(forms.Field):
    def validate(self, value):
        if value not in ('file', 'link'):
            return ValidationError('No option choosed')


class ResourceFileWidget(forms.widgets.FileInput):
    template_name = 'admin/forms/widgets/resources/file.html'


class ResourceLinkWidget(forms.widgets.URLInput):
    template_name = 'admin/forms/widgets/resources/url.html'


class ResourceListForm(forms.ModelForm):
    link = forms.HiddenInput(attrs={'required': False})
    file = forms.HiddenInput(attrs={'required': False})


class ChangeResourceForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.Textarea(
            attrs={'style': 'width: 99%', 'rows': 1}),
        label=_("Title")
    )
    description = forms.CharField(widget=CKEditorWidget, label=_("Description"))
    description_en = forms.CharField(widget=CKEditorWidget, label=_("Description") + " (EN)", required=False)

    def clean_status(self):
        dataset = self.instance.dataset

        if self.cleaned_data['status'] == 'published' and dataset.status == 'draft':
            error_message = _(
                "You can't set status of this resource to published, because it's dataset is still a draft. "
                "You should first published that dataset: "
            )

            error_message += "<a href='{}'>{}</a>".format(
                reverse('admin:datasets_dataset_change', args=[dataset.id]),
                dataset.title
            )

            raise forms.ValidationError(mark_safe(error_message))

        return self.cleaned_data['status']

    class Meta:
        labels = {
            'created': _("Availability date"),
            'modified': _("Modification date"),
            'verified': _("Update date"),
        }


class AddResourceForm(forms.ModelForm):
    switcher = ResourceSwitcherField(label=_('Data source'), widget=ResourceSourceSwitcher)
    file = forms.FileField(label=_('File'), widget=ResourceFileWidget)
    link = forms.URLField(widget=ResourceLinkWidget(attrs={'style': 'width: 99%'}))
    title = forms.CharField(
        widget=forms.Textarea(
            attrs={'style': 'width: 99%', 'rows': 1}),
        label=_("Title")
    )
    description = forms.CharField(widget=CKEditorWidget, label=_("Description"))
    description_en = forms.CharField(widget=CKEditorWidget, label=_("Description") + " (EN)", required=False)

    data_date = forms.DateField(initial=today(), widget=AdminDateWidget)

    def clean_link(self):
        value = self.cleaned_data.get('link')
        if not value:
            return None
        return value

    def clean_switcher(self):
        switcher_field = self.fields['switcher']
        selected_field = switcher_field.widget.value_from_datadict(self.data, self.files, self.add_prefix('switcher'))
        if selected_field == 'file':
            self.fields['link'].required = False
        elif selected_field == 'link':
            self.fields['file'].required = False
            self.fields['data_date'].required = False
        return selected_field

    def clean_status(self):
        dataset = self.cleaned_data.get('dataset')

        if dataset and dataset.status == 'draft':
            if self.cleaned_data['status'] == 'published':
                error_message = _(
                    "You can't set status of this resource to published, because it's dataset is still a draft. "
                    "Set status of this resource to draft or set stauts to published for that dataset: "
                )

                error_message += "<a href='{}'>{}</a>".format(
                    reverse('admin:datasets_dataset_change', args=[dataset.id]),
                    dataset.title
                )

                raise forms.ValidationError(mark_safe(error_message))

        return self.cleaned_data['status']

    def clean_data_date(self):
        data_date = self.cleaned_data.get('data_date')
        if not data_date:
            self.cleaned_data['data_date'] = today()
        return self.cleaned_data['data_date']

    class Media:
        js = (
            "https://gitcdn.github.io/bootstrap-toggle/2.2.2/js/bootstrap-toggle.min.js",
        )
        css = {
            'all': [
                "https://gitcdn.github.io/bootstrap-toggle/2.2.2/css/bootstrap-toggle.min.css",
            ]
        }


class TrashResourceForm(forms.ModelForm):

    def clean_is_removed(self):
        dataset = self.instance.dataset

        if self.cleaned_data['is_removed'] is False and dataset.is_removed:
            error_message = _(
                "You can't restore this resource, because it's dataset is still removed. Please first restore dataset: "
            )

            error_message += "<a href='{}'>{}</a>".format(
                reverse('admin:datasets_datasettrash_change', args=[dataset.id]),
                dataset.title
            )

            raise forms.ValidationError(mark_safe(error_message))

        return self.cleaned_data['is_removed']
