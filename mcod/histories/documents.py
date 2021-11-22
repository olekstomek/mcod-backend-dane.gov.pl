import json

from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from mcod.histories.models import History, LogEntry
from mcod import settings as mcs
from mcod.core.db.elastic import Document


@registry.register_document
class HistoriesDoc(Document):
    id = fields.IntegerField()
    table_name = fields.TextField()
    row_id = fields.IntegerField()
    action = fields.TextField()
    new_value = fields.TextField()
    difference = fields.TextField(attr='difference')
    change_user_id = fields.IntegerField()
    change_timestamp = fields.DateField()
    message = fields.TextField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['histories']
        settings = {
            'number_of_shards': 3,
            'number_of_replicas': 1
        }

    class Django:
        model = History

    def prepare_new_value(self, instance):
        return json.dumps(instance.new_value)

    def get_queryset(self):
        return super().get_queryset().exclude(table_name="user")


@registry.register_document
class LogEntryDoc(Document):
    table_name = fields.TextField()
    row_id = fields.IntegerField()
    action_name = fields.TextField()
    id = fields.IntegerField()
    difference = fields.TextField()
    change_user_id = fields.IntegerField()
    change_timestamp = fields.DateField()
    message = fields.TextField()

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['logentries']
        settings = {
            'number_of_shards': 3,
            'number_of_replicas': 1
        }

    class Django:
        model = LogEntry

    def get_queryset(self):
        return LogEntry.objects.for_admin_panel().exclude(content_type__model='user')
