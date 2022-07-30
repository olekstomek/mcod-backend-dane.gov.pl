import os

from dal import autocomplete, forward
import magic
from dateutil.utils import today
from django import forms
from django.contrib.admin.widgets import AdminDateWidget, FilteredSelectMultiple
from django.contrib.postgres.forms.jsonb import JSONField
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from mcod import settings
from mcod.lib.field_validators import ContainsLetterValidator
from mcod.lib.widgets import (
    CheckboxSelect,
    CKEditorWidget,
    ResourceDataRulesWidget,
    ResourceDataSchemaWidget,
    ResourceMapsAndPlotsWidget,
)
from mcod.regions.fields import RegionsMultipleChoiceField
from mcod.resources.archives import is_password_protected_archive_file
from mcod.resources.models import SUPPORTED_FILE_EXTENSIONS, Resource, ResourceFile, Supplement
from mcod.special_signs.models import SpecialSign
from mcod.unleash import is_enabled

RESOURCE_LANGUAGE_ENABLED = is_enabled('S53_resource_language.be')


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
        ones = {
            'b': _('latitude'),
            'l': _('longitude'),
            'postal_code': _('postal code'),
            'place': _('place'),
            'house_number': _('house number'),
            'uaddress': _('universal address'),
            'label': _('label'),
        }
        for k, v in ones.items():
            if names.count(k) > 1:
                raise ValidationError(
                    f'{_("element")} {v} {_("occured more than once")}. {_("Redefine the map by selecting only once the required element of the map set.")}')  # noqa

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
    regions = RegionsMultipleChoiceField(required=False, label=_('Regions'))
    has_dynamic_data = forms.ChoiceField(
        required=True,
        label=_('dynamic data').capitalize(),
        choices=[(True, _('Yes')), (False, _('No'))],
        help_text=(
            'Wskazanie TAK oznacza, że zasób jest traktowany jako dane dynamiczne.<br><br>Jeżeli chcesz się '
            'więcej dowiedzieć na temat danych dynamicznych <a href="%(url)s" target="_blank">przejdź do strony'
            '</a>') % {'url': f'{settings.BASE_URL}{settings.DYNAMIC_DATA_MANUAL_URL}'},
        widget=CheckboxSelect(attrs={'class': 'inline'}),
    )
    has_high_value_data = forms.ChoiceField(
        required=True,
        label=_('has high value data').capitalize(),
        choices=[(True, _('Yes')), (False, _('No'))],
        help_text=(
            'Wskazanie TAK oznacza, że zasób jest traktowany jako dane o wysokiej wartości.<br><br>Jeżeli chcesz '
            'się więcej dowiedzieć na temat danych o wysokiej wartości <a href="%(url)s" target="_blank">przejdź '
            'do strony</a>') % {'url': f'{settings.BASE_URL}{settings.HIGH_VALUE_DATA_MANUAL_URL}'},
        widget=CheckboxSelect(attrs={'class': 'inline'}),
    )
    if is_enabled('S47_research_data.be'):
        has_research_data = forms.ChoiceField(
            required=True,
            label=_('has research data').capitalize(),
            choices=[(True, _('Yes')), (False, _('No'))],
            help_text=(
                'Wskazanie TAK oznacza, że zasób jest traktowany jako dane badawcze.<br><br>Jeżeli chcesz '
                'się więcej dowiedzieć na temat danych badawczych <a href="%(url)s" target="_blank">przejdź '
                'do strony</a>') % {'url': f'{settings.BASE_URL}{settings.RESEARCH_DATA_MANUAL_URL}'},
            widget=CheckboxSelect(attrs={'class': 'inline'}),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'related_resource' in self.fields and RESOURCE_LANGUAGE_ENABLED:
            self.fields['related_resource'].label_from_instance = lambda obj: obj.label_from_instance
            self.fields['related_resource'].widget = autocomplete.ModelSelect2(
                url='resource-autocomplete',
                attrs={'data-html': True},
                forward=['dataset', forward.Const(self.instance.id, 'id')])
            # https://stackoverflow.com/a/42629593/1845230
            self.fields['related_resource'].widget.choices = self.fields['related_resource'].choices

    def clean(self):
        data = super().clean()
        dataset = data.get('dataset')
        data_date_err = Resource.get_auto_data_date_errors(data)
        if data_date_err:
            self.add_error(data_date_err.field_name, data_date_err.message)
        if data['status'] == 'published' and dataset and dataset.status == 'draft':
            error_message = _(
                "You can't set status of this resource to published, because it's dataset is still a draft. "
                "You should first published that dataset: ")
            self.add_error('status', mark_safe(error_message + dataset.title_as_link))
        related_resource = data.get('related_resource')
        if related_resource and related_resource not in dataset.resources.all():
            self.add_error('related_resource', _('Only resource from related dataset resources is valid!'))
        return data


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

        super().__init__(*args, **kwargs)
        if hasattr(self, 'instance'):
            self.fields['tabular_data_schema'].widget.instance = self.instance
            self.fields['data_rules'].widget.instance = self.instance
            self.fields['maps_and_plots'].widget.instance = self.instance
            if 'regions' in self.fields:
                self.fields['regions'].choices = self.instance.regions.all().values_list('region_id', 'hierarchy_label')

    def clean(self):
        data = super().clean()
        # `tabular_data_schema` field's widget modifies original `self.instance.tabular_data_schema`
        # then `maps_and_plots` field's widget makes use (and also modify) `self.instance.tabular_data_schema`.
        # Thanks to that `maps_and_plots` validators can make use of newest (if modified) column types.
        # In the result, the correct new value of `tabular_data_schema` is in both:
        # - `self.instance.tabular_data_schema` and `data['maps_and_plots']`.
        # TODO refactor
        data['tabular_data_schema'] = self.instance.tabular_data_schema
        return data

    class Meta:
        model = Resource
        exclude = ["old_resource_type", ]
        labels = {
            'created': _("Availability date"),
            'modified': _("Modification date"),
            'verified': _("Update date"),
            'is_chart_creation_blocked': _('Do not allow user charts to be created'),
            'main_file': _('File'),
            'csv_converted_file': _("File as CSV"),
            'jsonld_converted_file': _("File as JSON-LD"),
            'main_file_info': _('File info'),
            'main_file_encoding': _('File encoding')
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
    link = forms.URLField(widget=ResourceLinkWidget(attrs={'style': 'width: 99%', 'placeholder': 'https://'}))

    regions_ = RegionsMultipleChoiceField(required=False, label=_('Regions'))

    def clean_link(self):
        link = super().clean_link()
        if link and not link.startswith('https:'):
            self.add_error('link', _('Required scheme is https://'))
        return link

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
            elif is_password_protected_archive_file(file):
                self.add_error('file', _('Password protected archives are not allowed.'))
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


class ResourceInlineFormset(forms.models.BaseInlineFormSet):

    def save_new(self, form, commit=True):
        file = None
        if commit:
            file = form.cleaned_data.pop('file')
            form.instance.file = None
        instance = super().save_new(form, commit=commit)
        if file and instance.pk:
            ResourceFile.objects.create(
                resource=instance,
                is_main=True,
                file=file
            )
        # hack for dealing with bug described in https://code.djangoproject.com/ticket/12203 and
        # https://code.djangoproject.com/ticket/22852
        # It allows saving regions which are ManyToMany field with custom through model in InlineModelAdmin
        regions_data = form.cleaned_data.get('regions_')
        if regions_data and instance.id:
            for f in instance._meta.many_to_many:
                if f.name == 'regions':
                    f.save_form_data(instance, regions_data)
        return instance


class SupplementForm(forms.ModelForm):

    class Meta:
        model = Supplement
        fields = '__all__'
        labels = {
            'file': _('Add file'),
            'name': _('Document name'),
            'name_en': _('Document name') + ' (EN)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # hack to validate empty forms in formset, more:
        # https://stackoverflow.com/questions/4481366/django-and-empty-formset-are-valid
        self.empty_permitted = False

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            file_error = _('The wrong document format was selected!')
            mime = magic.from_buffer(file.read(2048), mime=True)
            if mime not in settings.ALLOWED_SUPPLEMENT_MIMETYPES:
                self.add_error('file', file_error)
            has_txt_extension = file.name.lower().endswith('.txt')
            if mime == 'text/plain' and not has_txt_extension:
                self.add_error('file', file_error)
        return file
