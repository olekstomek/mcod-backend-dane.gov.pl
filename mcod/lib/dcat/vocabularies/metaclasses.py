from django.forms.models import ModelFormMetaclass

from mcod.lib.dcat.vocabularies.manager import VocabulariesManager
from mcod.unleash import is_enabled


class DcatVocabAdminFormMetaClass(ModelFormMetaclass):
    """
    Metaclass for custom admin form with dynamic fields
    """
    def __new__(mcs, name, bases, attrs):
        new_class = super(DcatVocabAdminFormMetaClass, mcs).__new__(mcs, name, bases, attrs)
        if is_enabled('dcat_vocabularies.be'):
            vocab_manager = VocabulariesManager(new_class._meta.model.__name__)
            new_class.declared_fields.update(vocab_manager.set_vocabulary_choice_fields())
        return new_class
