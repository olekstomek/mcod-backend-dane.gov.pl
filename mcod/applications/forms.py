from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from mcod.applications.models import Application
from mcod.datasets.models import Dataset
from mcod.core.db.models import STATUS_CHOICES


class ApplicationForm(forms.ModelForm):
    title = forms.CharField(
        required=True,
        label=_("Title"),
        max_length=300,
        widget=forms.Textarea(attrs={'style': 'width: 99%', 'rows': 1})
    )
    slug = forms.CharField(required=False)
    notes = forms.CharField(widget=CKEditorUploadingWidget, required=True, label=_("Notes"))
    notes_en = forms.CharField(widget=CKEditorUploadingWidget, required=False, label=_("Notes")+" (EN)")
    datasets = forms.ModelMultipleChoiceField(
        queryset=Dataset.objects.filter(status=STATUS_CHOICES[0][0]),
        required=False,
        widget=FilteredSelectMultiple(_('datasets'), False),
        label=_("Dataset")
    )

    class Meta:
        model = Application
        fields = [
            'title',
            'slug',
            'notes',
            'author',
            'url',
            'image',
            'status',
            'datasets',
            'tags'
        ]
