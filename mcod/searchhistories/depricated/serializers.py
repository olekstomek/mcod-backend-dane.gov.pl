import marshmallow as ma
import marshmallow_jsonapi as ja

from mcod.lib.serializers import BasicSerializer


class UserSchema(ma.Schema):
    id = ma.fields.Int()


class SearchHistorySchema(ja.Schema):
    id = ma.fields.Int(dump_only=True)
    url = ma.fields.Str()
    query_sentence = ma.fields.Str()
    user = ma.fields.Nested(UserSchema, many=False)
    modified = ma.fields.Str()

    class Meta:
        type_ = "searchhistory"
        strict = True
        self_url_many = '/searchhistories'
        self_url = "/searchhistories/{searchhistory_id}"
        self_url_kwargs = {"searchhistory_id": "<id>"}


class SearchHistorySerializer(SearchHistorySchema, BasicSerializer):
    class Meta:
        type_ = "searchhistory"
        strict = True
        self_url_many = '/searchhistories'
        self_url = "/searchhistories/{searchhistory_id}"
        self_url_kwargs = {"searchhistory_id": "<id>"}
