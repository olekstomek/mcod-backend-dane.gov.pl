import abc
import json
import logging

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.translation import get_language
from django_redis import get_redis_connection
from lxml import etree
from redis.exceptions import ConnectionError

from mcod.core.storages import get_storage

logger = logging.getLogger('mcod')


class BaseVocabularyProcessor(metaclass=abc.ABCMeta):

    def __init__(self, file_url, filename, dict_name, many=False):
        self._choices = [('None', '---')] if not many else []
        self.file_url = file_url
        self.filename = filename
        self.dict_name = dict_name
        self.vocab_storage = get_storage('dcat_vocabularies')

    @abc.abstractmethod
    def get_queryset(self, *args, **kwargs):
        """
        Query the storage for result
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_form_choices(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def process_file(self):
        raise NotImplementedError

    @abc.abstractmethod
    def download_file(self):
        raise NotImplementedError


class XMLVocabularyProcessor(BaseVocabularyProcessor):

    def __init__(self, file_url, filename, dict_name, many=False):
        super(XMLVocabularyProcessor, self).__init__(file_url, filename, dict_name, many)
        try:
            redis_connection = settings.VOCABULARY_REDIS_CACHE
        except AttributeError:
            redis_connection = 'default'
        self.redis_connection = get_redis_connection(redis_connection)

    def process_file(self):
        try:
            root = etree.parse(self.vocab_storage.path(self.filename))
            parsed_data = self._process_content(root)
            self.redis_connection.set(self.dict_name, json.dumps(parsed_data))
        except OSError as err:
            logger.warning(f'Couldn\'t process file {self.filename} for controlled vocabulary processor'
                           f' {self.dict_name}. {err}')

    def get_queryset(self, *args, **kwargs):
        try:
            return json.loads(self.redis_connection.get(self.dict_name))
        except TypeError:
            return {}
        except ConnectionError as err:
            logger.warning(f'Couldn\'t connect to redis. {err}')
            return {}

    def download_file(self):
        requested_file = requests.get(self.file_url, allow_redirects=True)
        self.vocab_storage.save(self.filename, ContentFile(requested_file.content))

    def _process_content(self, parsed_data):
        raise NotImplementedError

    def reinitialize_cache_data(self):
        if not self.redis_connection.get(self.dict_name):
            self.process_file()

    def get_form_choices(self, *args, **kwargs):
        result = self.get_queryset()
        self._choices +=\
            [(key_name, descriptions.get(f'{get_language()}_label', 'en_label'))
             for key_name, descriptions in result.items()]
        return tuple(self._choices)


class AuthorityVocabularyProcessor(XMLVocabularyProcessor):

    def _process_content(self, parsed_data):
        result = {}
        pol_label = None
        en_label = None
        auth_code = None
        for record in parsed_data.iter():
            if record.tag == 'authority-code':
                auth_code = record.text
            elif record.tag == 'label':
                for label in record.iter():
                    label_attrs = label.attrib
                    lang_attr = label_attrs.get('lg')
                    if lang_attr == 'pol':
                        pol_label = label.text
                    if lang_attr == 'eng':
                        en_label = label.text
                    result[auth_code] = {
                        'en_label': en_label,
                        'pl_label': pol_label
                    }
        return result


class LanguageVocabularyProcessor(XMLVocabularyProcessor):

    def _process_content(self, parsed_data):
        result = {
            'POL': {
                'en_label': 'Polish',
                'pl_label': 'polski'
            },
            'ENG': {
                'en_label': 'English',
                'pl_label': 'angielski'
            }
        }
        return result
