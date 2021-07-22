import json

from mcod.lib.widgets import JsonPairDatasetInputs


class ExternalDatasetsWidget(JsonPairDatasetInputs):
    template_name = 'admin/forms/widgets/applications/external_datasets.html'

    def __init__(self, *args, **kwargs):
        kwargs['val_attrs'] = {'size': 35}
        kwargs['key_attrs'] = {'class': 'large'}
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget as an HTML string."""
        context = self.get_context(name, value, attrs)
        return self._render(self.template_name, context, renderer)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['items_list'] = json.loads(value) or [{'url': '', 'title': ''}]
        return context

    def value_from_datadict(self, data, files, name):
        result = []
        if 'json_key[customfields]' in data and 'json_value[customfields]' in data:
            titles = data.getlist('json_key[customfields]')
            urls = data.getlist('json_value[customfields]')
            for title, url in zip(titles, urls):
                if len(title) > 0 and title != 'key':
                    result.append({'title': title, 'url': url})
        return json.dumps(result)

    class Media:
        extend = False
        css = {
            'all': ('admin/css/customfields.css',)
        }
