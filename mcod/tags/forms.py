from django import forms
from django.core.exceptions import ValidationError

from mcod.applications.documents import Tag


class TagForm(forms.ModelForm):

    def clean_name(self):
        data = self.cleaned_data
        if data.get('name') != self.initial.get('name') and Tag.objects.filter(name__iexact=data.get('name')):
            raise ValidationError("Tag istnieje")
        return data['name']

    class Meta:
        model = Tag
        fields = ['name']
