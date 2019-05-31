from django.dispatch import Signal

watcher_updated = Signal(providing_args=['instance', 'prev_value', 'obj_state'])
query_watcher_created = Signal(providing_args=['instance', 'created_at'])
