from django.conf import settings
from falcon.routing import BaseConverter


class ExportFormatConverter(BaseConverter):
    def convert(self, value):
        return value if value in list(settings.EXPORT_FORMAT_TO_MIMETYPE.keys()) else None


class RDFFormatConverter(BaseConverter):
    def convert(self, value):
        return value if value in list(settings.RDF_FORMAT_TO_MIMETYPE.keys()) else None
