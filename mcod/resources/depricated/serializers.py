

# class ResourceSchema(BasicSchema):
#     id = ma.fields.Int(dump_only=True)
#     uuid = ma.fields.Str()
#     title = TranslatedStr()
#     description = TranslatedStr()
#     category = ma.fields.Str()
#     format = ma.fields.Str()
#     type = ma.fields.Str()
#     downloads_count = ma.fields.Integer()
#     openness_score = ma.fields.Integer()
#     views_count = ma.fields.Integer()
#     modified = ma.fields.Str()
#     created = ma.fields.Str()
#     verified = ma.fields.Str()
#     data_date = ma.fields.Date()
#     file_url = ma.fields.Str()
#     download_url = ma.fields.Str()
#     link = ma.fields.Str()
#     file_size = ma.fields.Integer()
#     visualization_types = ma.fields.List(ma.fields.Str())
#
#     class Meta:
#         type_ = 'resource'
#         strict = True
#         self_url_many = "/resources"
#         self_url = '/resources/{resource_id}'
#         self_url_kwargs = {"resource_id": "<id>"}
