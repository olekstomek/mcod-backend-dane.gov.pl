import os

from dateutil.utils import today
from django import forms
from django.contrib.admin.widgets import AdminDateWidget, FilteredSelectMultiple
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.forms.jsonb import JSONField

from mcod import settings
from mcod.lib.field_validators import ContainsLetterValidator
from mcod.lib.widgets import (
    CKEditorWidget,
    ResourceDataRulesWidget,
    ResourceDataSchemaWidget,
    ResourceMapsAndPlotsWidget,
)
from mcod.resources.archives import ARCHIVE_EXTENSIONS
from mcod.resources.models import Resource, supported_formats_choices
from mcod.special_signs.models import SpecialSign


SUPPORTED_FILE_EXTENSIONS = [f'.{x[0]}' for x in supported_formats_choices()]
SUPPORTED_FILE_EXTENSIONS.extend([f'.{x}' for x in ARCHIVE_EXTENSIONS])


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


def names_repr(names):
    names = map(_, names)
    names = map(str, names)
    names = ", ".join(list(names))
    return names


class MapsJSONField(JSONField):

    def validate(self, value):
        super().validate(value)
        fields = value.get('fields')
        if fields:
            names = [x.get('geo') for x in fields if x.get('geo')]
            self.only_one_x_validator(names)
            self.from_different_sets(names)
            self.complete_group(names)
            self.coordinates_should_be_numeric(fields)

    def only_one_x_validator(self, names):
        ones = ['b', 'l', 'postal_code', "place", "house_number", "uaddress", "label"]
        for v in ones:
            if names.count(v) > 1:
                raise ValidationError(
                    f'{_("element")} {_(v)} {_("occured more than once")}. {_("Redefine the map by selecting only once the required element of the map set.")}')  # noqa

    def from_different_sets(self, names):
        groups = {'coordinates': ["b", "l"],
                  'uaddress': ['uaddress'],
                  'address': ['house_number', 'place', 'postal_code', 'street']}
        membership = set()
        names = set(names)
        if 'label' in names:
            names.remove('label')

        for p in names:
            for k, g in groups.items():
                if p in g:
                    membership.add(k)
        if len(membership) > 1:
            err_msg = _("Selected items {} come from different map data sets.").format(names_repr(names))
            err_msg += str(_(' Redefine the map by selecting items from only one map data set.'))
            raise ValidationError(err_msg)

    def complete_group(self, names):
        groups = [
            ({"label", "b", "l"}, 'geographical coordinates'),
            ({"label", 'uaddress'}, 'universal address'),
            ({"label", "place", "postal_code"}, 'address'),
            ({"label", "house_number", "place", "postal_code"}, 'address'),
            ({"label", 'house_number', 'place', 'postal_code', 'street'}, 'address'),
        ]
        if names:
            names = set(names)

            for g in groups:
                if names == g[0]:
                    return

            if names == {'label'}:
                if self.widget.instance.format == "shp":
                    return
                raise ValidationError(_("The map data set is incomplete."))
            else:
                for g in groups:
                    if names.issubset(g[0]):
                        missing = names_repr(g[0] - names)
                        err_msg = _("Missing elements: {} for the map data set: {}.").format(missing, _(g[1]))
                        err_msg += str(_(" Redefine the map by selecting the selected items."))
                        raise ValidationError(err_msg)

                raise ValidationError(_("The map data set is incomplete."))

    @staticmethod
    def coordinates_should_be_numeric(fields):
        for f in fields:
            geo = f.get('geo')
            f_type = f.get('type')
            if geo == 'l' and f_type not in ['integer', 'number']:
                raise ValidationError(_("Longitude should be a number"))
            if geo == 'b' and f_type not in ['integer', 'number']:
                raise ValidationError(_("Latitude should be a number"))


class SpecialSignMultipleChoiceField(forms.ModelMultipleChoiceField):

    def label_from_instance(self, obj):
        return f'{obj.symbol} ({obj.name}) - {obj.description}'


class ResourceForm(forms.ModelForm):
    title = forms.CharField(widget=forms.Textarea(attrs={'style': 'width: 99%', 'rows': 2}), label=_("Title"))
    title_en = forms.CharField(
        widget=forms.Textarea(attrs={'style': 'width: 99%', 'rows': 2}), label=_("Title") + " (EN)", required=False)
    description = forms.CharField(
        widget=CKEditorWidget,
        label=_("Description"),
        min_length=settings.DESCRIPTION_FIELD_MIN_LENGTH,
        max_length=settings.DESCRIPTION_FIELD_MAX_LENGTH,
        validators=[ContainsLetterValidator()],
    )
    description_en = forms.CharField(
        widget=CKEditorWidget,
        label=_("Description") + " (EN)",
        required=False,
        min_length=settings.DESCRIPTION_FIELD_MIN_LENGTH,
        max_length=settings.DESCRIPTION_FIELD_MAX_LENGTH,
        validators=[ContainsLetterValidator()],
    )

    special_signs = SpecialSignMultipleChoiceField(
        queryset=SpecialSign.objects.published(), required=False, label=_('Special Signs'),
        widget=FilteredSelectMultiple(_('special signs'), False),
    )


class ChangeResourceForm(ResourceForm):
    tabular_data_schema = JSONField(
        widget=ResourceDataSchemaWidget(),
        required=False
    )

    data_rules = JSONField(
        widget=ResourceDataRulesWidget(),
        required=False
    )

    maps_and_plots = MapsJSONField(
        widget=ResourceMapsAndPlotsWidget(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            kwargs['initial'] = {
                'data_rules': kwargs['instance'].tabular_data_schema,
                'maps_and_plots': kwargs['instance'].tabular_data_schema,
            }

        super(ChangeResourceForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'instance'):
            self.fields['tabular_data_schema'].widget.instance = self.instance
            self.fields['data_rules'].widget.instance = self.instance
            self.fields['maps_and_plots'].widget.instance = self.instance

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
        model = Resource
        exclude = ["old_resource_type", ]
        labels = {
            'created': _("Availability date"),
            'modified': _("Modification date"),
            'verified': _("Update date"),
            'is_chart_creation_blocked': _('Do not allow user charts to be created'),
        }


class LinkOrFileUploadForm(forms.ModelForm):
    switcher = ResourceSwitcherField(label=_('Data source'), widget=ResourceSourceSwitcher)
    file = forms.FileField(label=_('File'), widget=ResourceFileWidget)
    link = forms.URLField(widget=ResourceLinkWidget(attrs={'style': 'width: 99%'}))

    def clean_link(self):
        value = self.cleaned_data.get('link')
        if not value:
            return None
        return value

    def clean_switcher(self):
        switcher_field = self.fields['switcher']
        selected_field = switcher_field.widget.value_from_datadict(self.data, self.files, self.add_prefix('switcher'))
        if self.instance and self.instance.id:
            self.fields['link'].required = self.fields['file'].required = False
            return selected_field

        if selected_field == 'file':
            self.fields['link'].required = False
        elif selected_field == 'link':
            self.fields['file'].required = False

        return selected_field


class AddResourceForm(ResourceForm, LinkOrFileUploadForm):
    data_date = forms.DateField(initial=today, widget=AdminDateWidget, label=_("Data date"))
    from_resource = forms.ModelChoiceField(queryset=Resource.objects.all(), widget=forms.HiddenInput(), required=False)

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

    def clean_switcher(self):
        selected_field = super().clean_switcher()
        if selected_field == 'link':
            self.fields['data_date'].required = False

    def clean_data_date(self):
        data_date = self.cleaned_data.get('data_date')
        if not data_date:
            self.cleaned_data['data_date'] = today()
        return self.cleaned_data['data_date']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            _name, ext = os.path.splitext(file.name)
            if ext.lower() not in SUPPORTED_FILE_EXTENSIONS:
                self.add_error('file', _('Invalid file extension: %(ext)s.') % {'ext': ext or '-'})
        return file


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
