from django_elasticsearch_dsl import fields

from mcod.lib.search.fields import TranslatedKeywordField


class CommonDocMixin(object):
    id = fields.Integer()
    object_name = fields.TextField(attr='object_name')
    api_url = fields.TextField(attr='api_url')


class ExtendedDocMixin(CommonDocMixin):
    slug = TranslatedKeywordField('slug')
    uuid = fields.TextField()
    status = fields.KeywordField()
    views_count = fields.IntegerField()
    published_at = fields.DateField()
    removed_at = fields.DateField()
