import pytest
from django.forms import MultipleChoiceField, ChoiceField

from mcod.unleash import is_enabled

if is_enabled('dcat_vocabularies.be'):
    class TestVocabulariesManager:

        def test_set_vocabulary_choice_field(self, vocabularies_manager):
            created_choice_fields = vocabularies_manager.set_vocabulary_choice_fields()
            assert 'single_choice_dummy_proc' in created_choice_fields
            assert 'multi_choice_dummy_proc' in created_choice_fields
            assert isinstance(created_choice_fields['single_choice_dummy_proc'], ChoiceField)
            assert isinstance(created_choice_fields['multi_choice_dummy_proc'], MultipleChoiceField)
            assert created_choice_fields['single_choice_dummy_proc'].choices == ['test_key', 'test_value']
            assert created_choice_fields['multi_choice_dummy_proc'].choices == ['test_key', 'test_value']

        @pytest.mark.parametrize('orig_vocabs, data_changed, cleaned_data, expected_vocab', [
            ({'single_choice_dummy_proc': 'old_val', 'multi_choice_dummy_proc': ['old_val', 'other_old_val']},
             ['single_choice_dummy_proc', 'multi_choice_dummy_proc'],
             {'single_choice_dummy_proc': 'new_val', 'multi_choice_dummy_proc': ['second_new_val', 'other_new_val']},
             {'expected_single': 'new_val', 'expected_multiple': ['second_new_val', 'other_new_val']}),
            (None, ['single_choice_dummy_proc', 'multi_choice_dummy_proc'],
             {'single_choice_dummy_proc': 'new_val', 'multi_choice_dummy_proc': ['second_new_val', 'other_new_val']},
             {'expected_single': 'new_val', 'expected_multiple': ['second_new_val', 'other_new_val']}),
            (None, ['single_choice_dummy_proc', 'multi_choice_dummy_proc'],
             {'single_choice_dummy_proc': 'None', 'multi_choice_dummy_proc': []},
             None),
            ({'single_choice_dummy_proc': 'old_val', 'multi_choice_dummy_proc': ['old_val', 'other_old_val']},
             ['single_choice_dummy_proc', 'multi_choice_dummy_proc'],
             {'single_choice_dummy_proc': 'None', 'multi_choice_dummy_proc': []},
             {'expected_single': None, 'expected_multiple': None})
        ])
        def test_update_object_vocabularies_update_selected(self, vocabularies_manager, orig_vocabs, data_changed,
                                                            cleaned_data, expected_vocab):
            new_vocabs = vocabularies_manager.update_object_vocabularies(orig_vocabs, data_changed, cleaned_data)
            try:
                assert new_vocabs.get('single_choice_dummy_proc') == expected_vocab['expected_single']
                assert new_vocabs.get('multi_choice_dummy_proc') == expected_vocab['expected_multiple']
            except AttributeError:
                assert new_vocabs is None
                assert expected_vocab is None
