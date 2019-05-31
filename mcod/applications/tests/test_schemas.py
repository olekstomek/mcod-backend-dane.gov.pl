from mcod.applications.depricated.schemas import ApplicationsList
from mcod.core.tests.helpers.elasticsearch import QuerysetTestHelper


class TestApplicationsList(object):
    class ApplicationsListTestSchema(QuerysetTestHelper, ApplicationsList):
        pass

    def test_empty_context(self, es_dsl_queryset):
        schema = self.ApplicationsListTestSchema()
        qs = schema.prepare_queryset(es_dsl_queryset, {}).to_dict()
        assert qs == {"query": {"match_all": {}}}

    def test_full_context(self, es_dsl_queryset):
        schema = self.ApplicationsListTestSchema()

        context = {
            'id': {
                'term': 'Blabla',
                'gte': '5',
                'gt': '4',
                'lte': '40',
                'lt': '41',
                'in': ['10', '50', '100']
            },
            'ids': ['46|3|1', '2'],
            'q': ['one', 'notes|two', 'three'],
            'tags': {
                'term': 'zxcv',
                'terms': ['dfg', 'asd'],
                'wildcard': '*abc*',
                'prefix': 'sth',
                'exclude': 'not_wanted'
            },
            'author': {
                'term': 'noone',
                'wildcard': '*one*',
                'prefix': 'dr.',
                'in': ['Tolkien', 'Orwell'],
                'exclude': 'Coelho'
            },
            'facet': ['tags', 'modified'],
            'sort': 'title',
            'highlight': ['notes'],
        }

        qs = schema.prepare_queryset(es_dsl_queryset, context).to_dict()

        assert 'query' in qs
        assert set(qs.keys()) == {'query', 'aggs', 'highlight', 'sort'}

        assert 'bool' in qs['query']
        query_bool = qs['query']['bool']
        sections = ('must', 'filter', 'should', 'must_not')
        assert set(query_bool.keys()) == (set(sections) | {'minimum_should_match'})

        assert all(type(query_bool[key]) == list for key in sections)

        musts = query_bool['must']
        assert len(musts) == 8
        nested = next(el for el in musts if 'nested' in el)
        nested_musts = nested['nested']['query']['bool']['must']
        assert len(nested_musts) == 4
        assert {'term': {'author': 'noone'}} in musts
        assert {'wildcard': {'author': '*one*'}} in musts
        assert {'prefix': {'author': 'dr.'}} in musts
        assert {'term': {'tags.pl': 'zxcv'}} in nested_musts
        assert {'wildcard': {'tags.pl': '*abc*'}} in nested_musts
        assert {'prefix': {'tags.pl': 'sth'}} in nested_musts
        assert {'term': {'id': 'Blabla'}} in musts

        for el in musts:
            if 'terms' in el:
                if 'author' in el['terms']:
                    assert set(el['terms']['author']) == {'Tolkien', 'Orwell'}
                if 'id' in el['terms']:
                    assert set(el['terms']['id']) == {'10', '50', '100'}
            if 'ids' in el:
                assert set(el['ids']['values']) == {'46', '3', '1', '2'}

        for el in nested_musts:
            if 'terms' in el and 'tags.pl' in el['terms']:
                assert set(el['terms']['tags.pl']) == {'dfg', 'asd'}

        must_nots = query_bool['must_not']
        assert len(must_nots) == 1
        nested_must_nots = nested['nested']['query']['bool']['must_not']
        assert len(nested_must_nots) == 1
        assert {'term': {'author': 'Coelho'}} in must_nots
        assert {'term': {'tags.pl': 'not_wanted'}} in nested_must_nots

        filters = query_bool['filter']
        assert len(filters) == 4
        assert {'range': {'id': {'gte': '5'}}} in filters
        assert {'range': {'id': {'lte': '40'}}} in filters
        assert {'range': {'id': {'gt': '4'}}} in filters
        assert {'range': {'id': {'lt': '41'}}} in filters

        shoulds = query_bool['should']
        assert len(shoulds) == 9

        values = {
            'title': ['one', 'three'],
            'notes': ['one', 'notes|two', 'three'],
            'datasets.title': ['one', 'three']
        }
        for field in ['title', 'notes', 'datasets.title']:
            for value in values[field]:
                assert {
                    'nested': {
                        'path': field,
                        'query': {
                            'bool': {
                                'should': [
                                    {
                                        'match': {
                                            f'{field}.pl': {
                                                'query': value,
                                                'fuzziness': 2,
                                                'fuzzy_transpositions': True
                                            }
                                        }
                                    }, {
                                        'match': {
                                            f'{field}.pl.asciied': {
                                                'query': value,
                                                'fuzziness': 2,
                                                'fuzzy_transpositions': True
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                } in shoulds

        aggs = qs['aggs']
        assert set(aggs.keys()) == {'_filter_modified', '_filter_tags'}
        assert 'aggs' in aggs['_filter_modified']
        assert 'modified' in aggs['_filter_modified']['aggs']
        assert 'date_histogram' in aggs['_filter_modified']['aggs']['modified']
        assert aggs['_filter_modified']['aggs']['modified']['date_histogram'] == {
            'field': 'modified',
            'interval': 'month',
            'size': 500,
            'min_doc_count': 0
        }

        assert 'aggs' in aggs['_filter_tags']
        assert 'tags' in aggs['_filter_tags']['aggs']
        assert 'terms' in aggs['_filter_tags']['aggs']['tags']
        assert 'field' in aggs['_filter_tags']['aggs']['tags']['terms']
        assert aggs['_filter_tags']['aggs']['tags']['terms']['field'] == 'tags'

        assert qs['sort'] == [{'title.pl.sort': {'nested': {'path': 'title'}, 'order': 'asc'}}]
        assert qs['highlight'] == {
            'fields': {
                'notes': {
                    'post_tags': ['</em>'],
                    'pre_tags': ['<em>']
                }
            }
        }
