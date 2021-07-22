from django_elasticsearch_dsl import fields

from mcod.watchers.models import ModelWatcher
from mcod.core.api.search.analyzers import lang_synonyms_analyzers, lang_exact_analyzers
from mcod.core.db.elastic import Document, NonIndexableValue
from mcod.lib.search.fields import TranslatedTextField, TranslatedKeywordsList, TranslatedSuggestField
from mcod import settings as mcs, settings


class ExtendedDocument(Document):
    NOTES_FIELD_NAME = 'notes'
    model = fields.KeywordField()
    slug = TranslatedTextField('slug')
    title = TranslatedSuggestField('title')
    title_synonyms = TranslatedTextField('title', analyzers=lang_synonyms_analyzers)
    title_exact = TranslatedTextField('title', analyzers=lang_exact_analyzers)
    notes = TranslatedTextField(NOTES_FIELD_NAME)
    notes_synonyms = TranslatedTextField(NOTES_FIELD_NAME, analyzers=lang_synonyms_analyzers)
    notes_exact = TranslatedTextField(NOTES_FIELD_NAME, analyzers=lang_exact_analyzers)
    tags = TranslatedKeywordsList()
    keywords = fields.NestedField(
        properties={
            'name': fields.KeywordField(),
            'language': fields.KeywordField()
        }
    )
    modified = fields.DateField()
    created = fields.DateField()
    verified = fields.DateField()
    search_date = fields.DateField()
    search_type = fields.KeywordField()
    status = fields.KeywordField()
    visualization_types = fields.KeywordField(multi=True)
    subscriptions = fields.NestedField(
        properties={
            'user_id': fields.IntegerField(),
            'subscription_id': fields.IntegerField()
        }
    )
    views_count = fields.IntegerField()

    def prepare_notes(self, instance):
        notes = getattr(instance, f'{self.NOTES_FIELD_NAME}_translated')
        return {
            lang_code: getattr(notes, lang_code)
            for lang_code in settings.MODELTRANS_AVAILABLE_LANGUAGES
        }
    prepare_notes_synonyms = prepare_notes
    prepare_notes_exact = prepare_notes

    def prepare_model(self, instance):
        return instance._meta.model_name

    def prepare_search_date(self, instance):
        return instance.created

    def prepare_tags(self, instance):
        return getattr(instance, 'tags_list', NonIndexableValue)

    def prepare_keywords(self, instance):
        return getattr(instance, 'keywords_list', NonIndexableValue)

    def prepare_verified(self, instance):
        return getattr(instance, 'verified', NonIndexableValue)

    def prepare_search_type(self, instance):
        return getattr(instance, 'search_type', NonIndexableValue)

    def prepare_visualization_types(self, instance):
        visualization_types = getattr(instance, 'visualization_types', NonIndexableValue)
        if isinstance(visualization_types, (tuple, list)) and len(visualization_types) == 0:
            visualization_types = ['none']
        return visualization_types

    def prepare_subscriptions(self, instance):
        try:
            watcher = ModelWatcher.objects.get_from_instance(instance)
            return [
                {'user_id': subscription.user_id, 'subscription_id': subscription.id} for subscription in
                watcher.subscriptions.all()
            ]
        except ModelWatcher.DoesNotExist:
            return []

    def get_queryset(self):
        return super().get_queryset().filter(status='published')


class SearchDoc(Document):
    model = fields.KeywordField()
    slug = TranslatedTextField('slug')
    title = TranslatedTextField('title')
    notes = TranslatedTextField('notes', raw_field_cls=fields.Text)

    title_synonyms = TranslatedTextField('title_synonyms',
                                         attr='title',
                                         analyzers=lang_synonyms_analyzers,
                                         properties=dict())
    notes_synonyms = TranslatedTextField('notes_synonyms',
                                         attr='notes',
                                         analyzers=lang_synonyms_analyzers,
                                         properties=dict())

    title_exact = TranslatedTextField('title_exact',
                                      attr='title',
                                      properties=dict(),
                                      analyzers=lang_exact_analyzers)
    notes_exact = TranslatedTextField('notes_exact',
                                      attr='notes',
                                      properties=dict(),
                                      analyzers=lang_exact_analyzers)

    modified = fields.DateField()
    created = fields.DateField()
    views_count = fields.IntegerField()
    search_date = fields.DateField()
    status = fields.KeywordField()
    visualization_types = fields.KeywordField(multi=True)

    subscriptions = fields.NestedField(
        properties={
            'user_id': fields.IntegerField(),
            'subscription_id': fields.IntegerField()
        }
    )

    def prepare_model(self, instance):
        return instance._meta.model_name

    def prepare_search_date(self, instance):
        return instance.created

    def prepare_subscriptions(self, instance):
        try:
            watcher = ModelWatcher.objects.get_from_instance(instance)
            return [
                {'user_id': subscription.user_id, 'subscription_id': subscription.id} for subscription in
                watcher.subscriptions.all()
            ]
        except ModelWatcher.DoesNotExist:
            return []

    def prepare_id(self, instance):
        return '{}-{}'.format(instance._meta.model_name, instance.pk)

    def prepare_visualization_types(self, instance):
        return ['none', ]

    def _prepare_action(self, object_instance, action):
        return {
            '_op_type': action,
            '_index': self._index._name,
            '_type': self._doc_type.name,
            '_id': self.prepare_id(object_instance),
            '_source': (
                self.prepare(object_instance) if action != 'delete' else None
            ),
        }

    class Index:
        name = mcs.ELASTICSEARCH_INDEX_NAMES['common']
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'max_result_window': 25000
        }
