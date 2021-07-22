from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.query import MoreLikeThis


def get_document_for_model(model):
    documents = registry.get_documents()
    for document in documents:
        if model == document._doc_type.model:
            return document


def get_index_and_mapping_for_model(model):
    document = get_document_for_model(model)
    if document is not None:
        return (
            document._doc_type.index,
            document._doc_type.mapping.properties.name
        )


def sort_by_list(unsorted_dict, sorted_keys):
    __unsorted_dict_keys = [__key for __key in unsorted_dict.keys()]
    __sorted_keys = (
        tuple(sorted_keys) + tuple(set(__unsorted_dict_keys) - set(sorted_keys))
    )
    for key in __sorted_keys:
        if key in unsorted_dict:
            unsorted_dict.move_to_end(key)

    return unsorted_dict


def more_like_this(obj, fields, max_query_terms=25, min_term_freq=2, min_doc_freq=5, max_doc_freq=0, query=None):
    _index, _mapping = get_index_and_mapping_for_model(obj._meta.model)

    if _index is None:
        return None

    _client = connections.get_connection()
    _search = Search(using=_client, index=_index)

    if query is not None:
        _search = _search.query(query)

    kwargs = {}

    if max_query_terms is not None:
        kwargs['max_query_terms'] = max_query_terms

    if min_term_freq is not None:
        kwargs['min_term_freq'] = min_term_freq

    if min_doc_freq is not None:
        kwargs['min_doc_freq'] = min_doc_freq

    if max_doc_freq is not None:
        kwargs['max_doc_freq'] = max_doc_freq

    return _search.query(
        MoreLikeThis(
            fields=fields,
            like={
                '_id': "{}".format(obj.pk),
                '_index': "{}".format(_index),
                '_type': "{}".format(_mapping)
            },
            **kwargs
        )
    )


# FIXME maybe locate somewhere better
def extract_script_field(search, field):
    for hit in search.hits._l_:
        setattr(hit, field, getattr(hit, field)[0])
