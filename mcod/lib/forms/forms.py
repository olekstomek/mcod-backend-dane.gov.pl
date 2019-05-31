from django.forms import Form, ModelForm, fields
from django.forms.utils import ErrorList

from mcod import settings
from mcod.lib.forms.fields import AnyChoiceField


class McodForm(Form):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=None,
                 empty_permitted=False, field_order=None, use_required_attribute=None, renderer=None, **kwargs):
        self._params = kwargs
        super().__init__(
            data=data, files=files, auto_id=auto_id, prefix=prefix,
            initial=initial, error_class=error_class, label_suffix=label_suffix,
            empty_permitted=empty_permitted, field_order=field_order, use_required_attribute=use_required_attribute,
            renderer=renderer
        )


class McodModelForm(ModelForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=None,
                 empty_permitted=False, field_order=None, use_required_attribute=None, renderer=None, **kwargs):
        self._params = kwargs
        super().__init__(
            data=data, files=files, auto_id=auto_id, prefix=prefix,
            initial=initial, error_class=error_class, label_suffix=label_suffix,
            empty_permitted=empty_permitted, field_order=field_order, use_required_attribute=use_required_attribute,
            renderer=renderer
        )


class PaginationForm(McodForm):
    page = fields.IntegerField(min_value=1, required=False)
    per_page = fields.IntegerField(min_value=0, max_value=settings.PER_PAGE_LIMIT, required=False)

    def clean_page(self):
        return self.cleaned_data.get('page') or 1

    def clean_per_page(self):
        return self.cleaned_data.get('per_page') or settings.PER_PAGE_DEFAULT


class SearchForm(PaginationForm):
    query = fields.CharField(required=False)
    filter = AnyChoiceField(required=False)
    sort = AnyChoiceField(required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.doc =
        if 'doc' in self._params:
            self.fields['filter'].choices = [('a', 'b'), ('c', 'd')]
            self.fields['sort'].choices = [('a', 'a'), ('s', 's')]

    # def clean(self):
    #     super

    # def clean_filter(self):
    #     if 'filter' in self.cleaned_data:
    #         if not isinstance(self.cleaned_data['filter'], list):
    #             self.cleaned_data['filter'] = list(self.cleaned_data['filter'])
    #
    # def clean_sort(self):
    #     if 'sort' in self.cleaned_data:
    #         if not isinstance(self.cleaned_data['sort'], list):
    #             self.cleaned_data['sort'] = list(self.cleaned_data['sort'])
