import marshmallow as ma
import marshmallow_jsonapi as ja
from functools import reduce

from mcod.lib.serializers import BasicSerializer, ArgsListToDict, SearchMeta, BucketItem


class StatsBucketItem(BucketItem):
    key = ma.fields.Raw(data_key='id')
    doc_count = ma.fields.Integer(data_key='count')


class ByMonthItem(StatsBucketItem):
    title = ma.fields.String(data_key='date', attribute='key_as_string')


class DocumentsByTypeBucketItem(StatsBucketItem):
    title = ma.fields.String(data_key='type')
    by_month = ma.fields.Nested(ByMonthItem(), attribute='by_month.buckets', many=True)
    monthly_avg = ma.fields.Method('get_monthly_avg', deserialize='load_monthly_avg')

    def get_monthly_avg(self, obj):
        lst = [item['doc_count'] for item in obj['by_month']['buckets']]
        avg = reduce(lambda x, y: x + y, lst) / len(lst)
        return avg

    def load_monthly_avg(self, value):
        return float(value)


class StatsAggregations(ArgsListToDict):
    documents_by_type = ma.fields.Nested(DocumentsByTypeBucketItem(), attribute='documents_by_type.buckets', many=True)
    datasets_by_institution = ma.fields.Nested(StatsBucketItem(app='organizations', model='Organization'),
                                               attribute='datasets_by_institution.inner.buckets', many=True)
    datasets_by_category = ma.fields.Nested(StatsBucketItem(app='categories', model='Category'),
                                            attribute='datasets_by_category.inner.buckets', many=True)
    datasets_by_formats = ma.fields.Nested(StatsBucketItem(), attribute='datasets_by_formats.buckets', many=True)
    datasets_by_tag = ma.fields.Nested(StatsBucketItem(), attribute='datasets_by_tag.buckets', many=True)
    datasets_by_openness_scores = ma.fields.Nested(StatsBucketItem(), attribute='datasets_by_openness_scores.buckets',
                                                   many=True)


class StatsMeta(SearchMeta):
    aggs = ma.fields.Nested(StatsAggregations, attribute='aggregations')


class StatsSchema(ja.Schema):
    id = ma.fields.Int()

    class Meta:
        type_ = 'stats'
        strict = True
        self_url = '/stats'


class StatsSerializer(StatsSchema, BasicSerializer):
    pass
