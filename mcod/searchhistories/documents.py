from django_elasticsearch_dsl import DocType, Index, fields
from mcod.searchhistories.models import SearchHistory
from mcod import settings

INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES['searchhistories'])
INDEX.settings(**settings.ELASTICSEARCH_DSL_INDEX_SETTINGS)


@INDEX.doc_type
class SearchHistoriesDoc(DocType):
    id = fields.IntegerField()
    url = fields.TextField()
    query_sentence = fields.TextField()
    user = fields.NestedField(
        attr='user',
        properties={
            'id': fields.IntegerField(),
        }
    )
    modified = fields.DateField()

    class Meta:
        doc_type = 'searchhistory'
        model = SearchHistory
