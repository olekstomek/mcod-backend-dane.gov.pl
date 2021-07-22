import itertools

from django import forms
from django.utils.translation import gettext_lazy as _

from mcod.tags.models import Tag
from mcod.tags.widgets import TagAutocompleteSelectMultiple, TagRelatedFieldWidgetWrapper
from mcod.unleash import is_enabled


class ModelFormWithKeywords(forms.ModelForm):
    tags_pl = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(language='pl'),
        required=False,
        label=_("Tags") + ' (PL)',
    )

    tags_en = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(language='en'),
        required=False,
        label=_("Tags") + ' (EN)',
    )

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)

        if is_enabled('S18_new_tags.be'):
            self._init_tags_fields(instance)
        else:
            self._remove_tags_fields()

        # TODO remove below condition on S18_new_tags.be removal
        if 'tags' in self.fields:
            self.fields['tags'].queryset = Tag.objects.filter(language='')

    def clean(self):
        data = super().clean()
        if not is_enabled('S18_new_tags.be') and self.instance and self.instance.id and 'tags' in data:
            # make it so saving tags without flag, won't remove new keywords (with language field filled)
            selected = data['tags'].values_list('id', flat=True)
            keywords = self.instance.tags.exclude(language='').values_list('id', flat=True)
            data['tags'] = Tag.objects.filter(id__in=itertools.chain(selected, keywords))
        return data

    @classmethod
    def recreate_tags_widgets(cls, request, db_field, admin_site):
        related_modeladmin = admin_site._registry.get(db_field.remote_field.model)
        wrapper_kwargs = {}
        if related_modeladmin:
            wrapper_kwargs.update(
                can_add_related=related_modeladmin.has_add_permission(request),
                can_change_related=related_modeladmin.has_change_permission(request),
                can_delete_related=related_modeladmin.has_delete_permission(request),
                can_view_related=related_modeladmin.has_view_permission(request),
            )

        for lang in ('pl', 'en'):
            widget = TagAutocompleteSelectMultiple(rel=db_field.remote_field, admin_site=admin_site, language=lang)
            wrapper = TagRelatedFieldWidgetWrapper(widget, db_field.remote_field, admin_site, language=lang, **wrapper_kwargs)
            cls.base_fields[f'tags_{lang}'].widget = wrapper

    def _init_tags_fields(self, instance):
        if 'tags' in self.fields:
            self.fields['tags'].required = False

        for lang in ('pl', 'en'):
            field_name = f'tags_{lang}'
            if field_name not in self.fields:
                continue
            if instance:
                self.fields[f'tags_{lang}'].initial = instance.tags.filter(language=lang)
            else:
                self.fields[f'tags_{lang}'].initial = Tag.objects.none()

    def _remove_tags_fields(self):
        for lang in ('pl', 'en'):
            field_name = f'tags_{lang}'
            if field_name not in self.fields:
                continue
            del self.fields[field_name]

    def _save_m2m(self):
        super()._save_m2m()
        if not is_enabled('S18_new_tags.be'):
            return
        # saving new keywords (with language field filled) shouldn't remove old tags (with language field unfilled)
        instance = self.instance
        # TODO remove exclude(language='') on S18_new_tags.be removal
        old_tags_ids = set(instance.tags.exclude(language='').values_list('id', flat=True))
        new_tags = []
        for tag in itertools.chain(self.cleaned_data.get('tags_pl', []), self.cleaned_data.get('tags_en', [])):
            if tag.id in old_tags_ids:
                old_tags_ids.remove(tag.id)
            else:
                new_tags.append(tag)
        instance.tags.remove(*old_tags_ids)
        instance.tags.add(*new_tags)


class TagForm(forms.ModelForm):
    lang_code = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_enabled('S18_new_tags.be') and 'language' in self.fields:
            self.fields['language'].required = False

    def has_field_changed(self, *names):
        return not all(self.cleaned_data.get(name) == self.initial.get(name) for name in names)

    def clean(self):
        cleaned_data = super().clean()
        if self.lang_code:
            cleaned_data['language'] = self.lang_code
        if self.has_field_changed('name', 'language') and Tag.objects.filter(
                name__iexact=cleaned_data.get('name'), language__iexact=cleaned_data.get('language')).exists():

            if is_enabled('S18_new_tags.be'):
                self.add_error('name', _("Tag already exists for specified language."))
            else:
                self.add_error('name', "Tag istnieje")
        return cleaned_data

    class Meta:
        model = Tag
        fields = ['name', 'language']
