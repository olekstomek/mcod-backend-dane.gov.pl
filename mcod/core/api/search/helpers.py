from django_elasticsearch_dsl.registries import registry


def get_document_for_model(model):
    documents = registry.get_documents()
    for document in documents:
        if model == document._doc_type.model:
            return document
