from django.contrib import admin
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from mcod.articles.forms import ArticleForm
from mcod.articles.models import Article, ArticleTrash
from mcod.lib.admin_mixins import (
    HistoryMixin,
    ModelAdmin,
    TrashMixin,
)


@admin.register(Article)
class ArticleAdmin(HistoryMixin, ModelAdmin):
    actions_on_top = True
    autocomplete_fields = ['tags']
    fieldsets = (
        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': (
                    "preview_link",
                    "title",
                )
            }
        ),

        (
            'url',
            {
                'classes': ('collapse', 'suit-tab', 'suit-tab-general',),
                'fields': (
                    "slug",
                )
            }
        ),

        (
            None,
            {
                'classes': ('suit-tab', 'suit-tab-general',),
                'fields': (
                    "notes",
                    'author',
                    'license',
                    'status',
                    'category'
                )
            }
        ),

        (
            _("Tags"),
            {
                'classes': ('suit-tab', 'suit-tab-tags',),
                'fields': ('tags_pl', 'tags_en'),
            }
        ),
    )
    form = ArticleForm
    lang_fields = True
    list_display = [
        'title',
        'status_label',
        'created_by_label',
        'category',
        'preview_link',
        'obj_history'
    ]
    list_filter = ['category', ]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ['preview_link']
    soft_delete = True
    search_fields = ["title", "created_by__email"]

    @property
    def suit_form_tabs(self):
        return (
            ('general', _('General')),
            *self.get_translations_tabs(),
            ('tags', _('Tags')),
        )

    def get_fieldsets(self, request, obj=None):
        return self.fieldsets + tuple(self.get_translations_fieldsets())

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.recreate_tags_widgets(request=request, db_field=Article.tags.field, admin_site=self.admin_site)
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        self.request = request
        return qs

    def preview_link(self, obj):
        return obj.preview_link

    preview_link.allow_tags = True
    preview_link.short_description = _('Preview link')

    def save_model(self, request, obj, form, change):
        if 'slug' in form.cleaned_data:
            if form.cleaned_data['slug'] == "":
                obj.slug = slugify(form.cleaned_data['title'])
        if not obj.id:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.save()

    class Media:
        js = ("articles/js/hide_license_buttons.js",)


@admin.register(ArticleTrash)
class ArticleTrashAdmin(HistoryMixin, TrashMixin):
    list_display = ['title', 'author']
    search_fields = ['title', 'author']

    fields = [
        'title',
        'author',
        'datasets',
        'notes',
        'slug',
        'status',
        'tags_list_pl',
        'tags_list_en',
        'license_id',
        'is_removed'
    ]
    readonly_fields = [
        'title',
        'author',
        'datasets',
        'notes',
        'slug',
        'status',
        'tags_list_pl',
        'tags_list_en',
        'license_id'
    ]

    def tags_list_pl(self, instance):
        return instance.tags_as_str(lang='pl')
    tags_list_pl.short_description = _('Tags') + ' (PL)'

    def tags_list_en(self, instance):
        return instance.tags_as_str(lang='en')
    tags_list_en.short_description = _('Tags') + ' (EN)'
