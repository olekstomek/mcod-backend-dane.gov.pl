# -*- coding: utf-8 -*-
import json
from datetime import datetime, date, time

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_text
from django.utils.functional import Promise


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


class DateTimeToISOEncoder(json.JSONEncoder):
    def default(self, data):
        if isinstance(data, (datetime, time)):
            return data.isoformat('T')
        if isinstance(data, date):
            return data.isoformat()
