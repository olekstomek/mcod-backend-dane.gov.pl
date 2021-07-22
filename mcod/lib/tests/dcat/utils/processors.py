from mcod.lib.dcat.vocabularies.processors import BaseVocabularyProcessor


class DummyProcessor(BaseVocabularyProcessor):

    def get_queryset(self, *args, **kwargs):
        return {'test_key': 'test_value'}

    def get_form_choices(self, *args, **kwargs):
        return 'test_key', 'test_value'

    def process_file(self):
        pass

    def download_file(self):
        pass
