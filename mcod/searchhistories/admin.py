from django.contrib import admin

from mcod.searchhistories.models import SearchHistory
from mcod.lib.admin_mixins import ModelAdmin


@admin.register(SearchHistory)
class SearchHistoryAdmin(ModelAdmin):
    list_display = ['id', 'user_id', 'query_sentence', "url"]
