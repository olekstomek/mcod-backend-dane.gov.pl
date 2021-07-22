import marshmallow as ma
from django.utils.translation import get_language

from mcod.unleash import is_enabled


class Tags(ma.fields.List):
    def _serialize(self, value, attr, obj, **kwargs):
        lang = get_language()
        if is_enabled('S18_new_tags.be'):
            names = [tag.name for tag in value.filter(language=lang)]
        else:
            names = [getattr(tag, f'name_{lang}') for tag in value.all()]
        return [
            name
            for name in names
            if name is not None
        ]
