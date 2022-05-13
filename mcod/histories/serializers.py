import json

from mcod.core.api import fields
from mcod.core.api.jsonapi.serializers import ObjectAttrs, TopLevel
from mcod.core.utils import anonymize_email
from mcod.unleash import is_enabled

IS_ANONYMOUS = is_enabled('S47_anonymize_history.be')


class HistoryApiAttrs(ObjectAttrs):
    action = fields.Str()
    change_timestamp = fields.DateTime()
    change_user_id = fields.Str()
    difference = fields.Method('get_difference')
    message = fields.Str()
    new_value = fields.Method('get_new_value')
    row_id = fields.Int()
    table_name = fields.Str()

    class Meta:
        strict = True
        ordered = True
        object_type = 'history'
        api_path = '/histories'
        url_template = '{api_url}/histories/{ident}'
        model = 'histories.History'

    def get_difference(self, obj):
        difference = json.loads(obj.difference) or {}
        if 'values_changed' in difference:
            if "root['password']" in difference['values_changed']:
                difference['values_changed']["root['password']"]['new_value'] = "********"
                difference['values_changed']["root['password']"]['old_value'] = "********"
        return difference

    def get_new_value(self, obj):
        new_value = obj.new_value if isinstance(obj.new_value, dict) else json.loads(obj.new_value)
        if new_value and 'password' in new_value:
            new_value['password'] = "**********"
        return new_value


class HistoryApiResponse(TopLevel):
    class Meta:
        attrs_schema = HistoryApiAttrs


class LogEntryApiAttrs(ObjectAttrs):
    action = fields.Str(attribute='action_name')
    change_timestamp = fields.DateTime()
    change_user_id = fields.Str()
    difference = fields.Method('get_difference')
    message = fields.Str()
    new_value = fields.Method('get_new_value')
    row_id = fields.Int()
    table_name = fields.Str()

    class Meta:
        strict = True
        ordered = True
        object_type = 'history'
        api_path = '/histories'
        url_template = '{api_url}/histories/{ident}'
        model = 'histories.LogEntry'

    def get_difference(self, obj):
        try:
            data = json.loads(obj.difference)
        except ValueError:
            data = {}
        for key, val in data.items():
            if obj.action_name == 'INSERT' and isinstance(val, list) and len(val) == 2:
                data[key] = val[1]
            value = data[key]
            if key in ['created_by', 'modified_by', 'update_notification_recipient_email'] and value and IS_ANONYMOUS:
                data[key] = [anonymize_email(x) for x in value] if isinstance(value, list) else anonymize_email(value)
        return data

    def get_new_value(self, obj):
        return self.get_difference(obj)


class LogEntryApiResponse(TopLevel):
    class Meta:
        attrs_schema = LogEntryApiAttrs
