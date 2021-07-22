from pydoc import locate

from django.conf import settings


class VocabulariesManager(object):

    def __init__(self, model_name=None):
        if model_name:
            self._vocabularies = settings.MODELS_DCAT_VOCABULARIES[model_name]
        else:
            self._vocabularies =\
                [vocab_name for vocab_name, vocab_settings in settings.VOCABULARY_SOURCES.items() if
                 vocab_settings.get('enabled', True)]

    @property
    def vocabularies(self):
        return self._vocabularies

    def set_vocabulary_choice_fields(self):
        dynamic_fields = {}
        for source_name in self._vocabularies:
            source_settings = settings.VOCABULARY_SOURCES[source_name]
            vocab_processor = self.initialize_processor(source_name, source_settings)
            form_field = locate(source_settings['choice_field_class'])
            dynamic_fields[source_name] =\
                form_field(choices=vocab_processor.get_form_choices(), label=source_settings['label'], required=False)
        return dynamic_fields

    def update_object_vocabularies(self, current_vocabs, changed_data, cleaned_data):
        for vocab_field in self._vocabularies:
            if vocab_field in changed_data:
                many = settings.VOCABULARY_SOURCES[vocab_field]['processor_kwargs'].get('many', False)
                empty_value = 'None' if not many else []
                vocab_value = cleaned_data.get(vocab_field, empty_value)
                if current_vocabs and vocab_value == empty_value and vocab_field in current_vocabs:
                    current_vocabs.pop(vocab_field)
                elif vocab_value != empty_value:
                    try:
                        current_vocabs[vocab_field] = vocab_value
                    except TypeError:
                        current_vocabs = {vocab_field: vocab_value}
        return current_vocabs

    @staticmethod
    def set_vocabulary_fields_initial(form, obj):
        current_vocabs = obj.dcat_vocabularies
        try:
            for vocab_name, vocab_value in current_vocabs.items():
                form.base_fields[vocab_name].initial = vocab_value
        except AttributeError:
            pass
        except KeyError:
            pass

    @staticmethod
    def initialize_processor(processor_name, source_settings):
        processor_class = locate(source_settings['processor_path'])
        kwargs = source_settings['processor_kwargs']
        kwargs['dict_name'] = processor_name
        return processor_class(**kwargs)

    def reinitialize_cache(self):
        for source_name in self._vocabularies:
            source_settings = settings.VOCABULARY_SOURCES[source_name]
            vocab_processor = self.initialize_processor(source_name, source_settings)
            try:
                vocab_processor.reinitialize_cache_data()
            except AttributeError:
                pass
