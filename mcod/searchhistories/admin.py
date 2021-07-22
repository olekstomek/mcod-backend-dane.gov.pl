from django.contrib import admin

# Register your models here.
from mcod.searchhistories.models import SearchHistory
from mcod.lib.admin_mixins import MCODAdminMixin


@admin.register(SearchHistory)
class SearchHistoryAdmin(MCODAdminMixin, admin.ModelAdmin):
    list_display = ['id', 'user_id', 'query_sentence', "url"]
