from mcod.lib.widgets import CKEditorUploadingWidget
from django import forms
from django.utils.translation import gettext_lazy as _

from mcod.articles.models import Article
from mcod.tags.forms import ModelFormWithKeywords


class ArticleForm(ModelFormWithKeywords):
    title = forms.CharField(
        required=True,
        label=_("Title"),
        max_length=300,
        widget=forms.Textarea(attrs={'style': 'width: 99%', 'rows': 2})
    )
    notes = forms.CharField(widget=CKEditorUploadingWidget, required=True, label=_("Notes"))
    notes_en = forms.CharField(widget=CKEditorUploadingWidget, required=False, label=_("Notes") + " (EN)")

    class Meta:
        model = Article
        fields = [
            'title',
            'slug',
            'notes',
            'author',
            'license',
            'status',
            'tags',
            'category',
        ]
