from django.contrib import admin
from mcod.histories.models import History


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'action', 'table_name', 'row_id', 'message']
    list_filter = ['action', 'table_name']
    search_fields = ['row_id']
    fields = [
        'table_name',
        'row_id',
        'action',
        'diff_prettified',
        'user',
        'change_timestamp'
    ]
    readonly_fields = [
        'table_name',
        'row_id',
        'action',
        'diff_prettified',
        'user',
        'change_timestamp'
    ]

    def has_add_permission(self, request):
        return False

    # def has_change_permission(self, request, obj=None):
    #     return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return History.objects.exclude(
            table_name__in=['member', 'application_tag', 'dataset_tag', 'article_tag', 'application_dataset'])
