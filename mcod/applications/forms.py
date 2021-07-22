from mcod.lib.widgets import CKEditorUploadingWidget
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.postgres.forms.jsonb import JSONField
from django.utils.translation import gettext_lazy as _

from mcod.applications.models import Application, ApplicationProposal
from mcod.applications.widgets import ExternalDatasetsWidget
from mcod.core.db.models import STATUS_CHOICES
from mcod.datasets.models import Dataset
from mcod.tags.forms import ModelFormWithKeywords


class ApplicationForm(ModelFormWithKeywords):
    title = forms.CharField(
        required=True,
        label=_("Title"),
        max_length=300,
        widget=forms.Textarea(attrs={'style': 'width: 99%', 'rows': 2})
    )
    slug = forms.CharField(required=False)
    notes = forms.CharField(widget=CKEditorUploadingWidget, required=True, label=_("Notes"))
    notes_en = forms.CharField(widget=CKEditorUploadingWidget, required=False, label=_("Notes") + " (EN)")
    datasets = forms.ModelMultipleChoiceField(
        queryset=Dataset.objects.filter(status=STATUS_CHOICES[0][0]),
        required=False,
        widget=FilteredSelectMultiple(_('datasets'), False),
        label=_("Dataset")
    )
    external_datasets = JSONField(
        label=_('External datasets'),
        widget=ExternalDatasetsWidget(),
        required=False)

    class Meta:
        model = Application
        fields = [
            'title',
            'slug',
            'notes',
            'author',
            'external_datasets',
            'url',
            'image',
            'illustrative_graphics',
            'illustrative_graphics_alt',
            'main_page_position',
            'status',
            'datasets',
            'tags'
        ]


class ApplicationProposalForm(forms.ModelForm):

    class Meta:
        model = ApplicationProposal
        fields = [
            'title',
            'url',
            'notes',
            'applicant_email',
            'author',
            'keywords',
            'comment',
            'report_date',
            'decision',
            'decision_date',
        ]
        labels = {
            'author': _('Application author'),
            'decision': _('Decision made'),
            'notes': _('Application notes'),
            'title': _('Application name'),
            'url': _('Application link / Application info page address'),
        }
        widgets = {
            'comment': forms.Textarea(attrs={'rows': '1', 'class': 'input-block-level'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'decision' in self.fields:
            self.fields['decision'].required = True
