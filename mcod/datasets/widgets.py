from django.forms import CheckboxInput


class CheckboxInputWithLabel(CheckboxInput):
    template_name = 'widgets/checkbox_labeled.html'

    def __init__(self, *args, label=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = label

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['label'] = self.label
        return context
