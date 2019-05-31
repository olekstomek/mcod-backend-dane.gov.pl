# encoding: utf-8
#  widget.py
#  apps
#
#  Created by antonin on 2012-12-17.
#  Copyright 2012 Ripple Motion. All rights reserved.
#

import json

from django.forms import Widget
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class JsonPairInputsWidget(Widget):
    def __init__(self, *args, **kwargs):
        """
        kwargs:
        key_attrs -- html attributes applied to the 1st input box pairs
        val_attrs -- html attributes applied to the 2nd input box pairs

        """
        self.key_attrs = {}
        self.val_attrs = {}
        if "key_attrs" in kwargs:
            self.key_attrs = kwargs.pop("key_attrs")
        if "val_attrs" in kwargs:
            self.val_attrs = kwargs.pop("val_attrs")
        super(JsonPairInputsWidget, self).__init__(*args, **kwargs)


class JsonPairDatasetInputs(JsonPairInputsWidget):

    def render(self, name, value, attrs=None, renderer=None):
        """Renders this widget into an html string

        args:
        name  (str)  -- name of the field
        value (str)  -- a json string of a two-tuple list automatically passed in by django
        attrs (dict) -- automatically passed in by django (unused in this function)
        """
        twotuple = json.loads(value)
        if not twotuple:
            twotuple = {}
            twotuple['key'] = 'value'

        ret = ''
        if value and len(value) > 0:
            for k, v in twotuple.items():
                key, value = _(k), v

                key_input = f'<input type="text" name="json_key[{name}]" value="{key}">'
                val_input = f'<input type="text" name="json_value[{name}]" value="{value}" class="customfields"><br>'

                ret += key_input + val_input
        return mark_safe(ret)

    def value_from_datadict(self, data, files, name):
        """
        Returns the simplejson representation of the key-value pairs
        sent in the POST parameters

        args:
        data  (dict)  -- request.POST or request.GET parameters
        files (list)  -- request.FILES
        name  (str)   -- the name of the field associated with this widget

        """

        customfields = {}
        if ('json_key[%s]' % name) in data and ('json_value[%s]' % name) in data:
            keys = data.getlist("json_key[%s]" % name)
            values = data.getlist("json_value[%s]" % name)
            for key, value in zip(keys, values):
                if len(key) > 0 and key != "key":
                    customfields[key] = value
        return json.dumps(customfields)

    class Media:

        js = ('admin/js/widgets/customfields.js',)
        css = {
            'all': ('admin/css/customfields.css',)
        }
