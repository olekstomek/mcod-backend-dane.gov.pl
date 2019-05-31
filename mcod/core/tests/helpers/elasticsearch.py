from django_elasticsearch_dsl.registries import registry


class ElasticCleanHelper(object):
    def setup_method(self):
        models = registry.get_models()
        for index in registry.get_indices(models):
            index.delete(ignore=404)
            index.create()

        # for doc in registry.get_documents(models):
        #     qs = doc().get_queryset()
        #     doc().update(qs)


class QuerysetTestHelper(object):
    def prepare_queryset(self, queryset, context):
        for name, field in self.fields.items():
            queryset = field.prepare_queryset(queryset, context=context.get(name, None))
        return queryset
