import io

import pandas as pd
from falcon.media import BaseHandler

from mcod.core.utils import XMLWriter, save_as_csv, save_as_xml
from mcod.settings import RDF_FORMAT_TO_MIMETYPE
from mcod.unleash import is_enabled


class RDFHandler(BaseHandler):
    def deserialize(self, stream, content_type, content_length):
        # Todo - to be implemented. For now do nothing
        return stream

    def serialize(self, media, content_type):
        if not hasattr(media, "serialize"):
            return media
        if content_type not in RDF_FORMAT_TO_MIMETYPE.values():
            content_type = RDF_FORMAT_TO_MIMETYPE["jsonld"]

        if content_type == "application/ld+json":
            result = media.serialize(
                format=content_type, auto_compact=True, encoding="utf-8"
            )
        else:
            result = media.serialize(format=content_type, encoding="utf-8")

        return result


class SparqlHandler(BaseHandler):
    def deserialize(self, stream, content_type, content_length):
        # Todo - to be implemented. For now do nothing
        return stream

    def serialize(self, media, content_type):
        print(content_type, media)
        return media


class XMLHandler(BaseHandler):
    def deserialize(self, stream, content_type, content_length):
        # Todo - to be implemented. For now do nothing
        return stream

    def serialize(self, context, content_type):
        output = context
        if hasattr(context, "serializer_schema") and hasattr(context, "data"):
            schema = context.serializer_schema
            xml_data = schema.dump(context.data)
            xml_file = io.StringIO()
            if is_enabled("S60_fix_for_task_creating_xml_and_csv_metadata_files.be"):
                writer_class: XMLWriter = XMLWriter()
                writer_class.save(file_object=xml_file, data=xml_data)
            else:
                save_as_xml(xml_file, xml_data)
            output = xml_file.getvalue().encode("utf-8")
        return output


class ExportHandler(BaseHandler):
    def deserialize(self, stream, content_type, content_length):
        # Todo - to be implemented. For now do nothing
        return stream

    def serialize(self, context, content_type):
        if content_type == "application/vnd.ms-excel":
            return self.to_xlsx(context)
        return self.to_csv(context)

    def to_csv(self, context):
        output = context
        if hasattr(context, "data"):
            csv_file = self._as_csv(context)
            output = csv_file.getvalue().encode("utf-8")
        return output

    def _as_csv(self, context):
        if not getattr(context, "serializer_schema", None):
            schema_class = context.data.model.get_csv_serializer_schema()
            exclude = (
                ["recommendation_state_name", "recommendation_notes"]
                if not context.full
                else []
            )
            if context.state == "planned":
                exclude += [
                    "is_resource_added_yes_no",
                    "resource_link",
                    "is_resource_added_notes",
                ]
            schema = schema_class(many=True, exclude=exclude)
        else:
            schema = context.serializer_schema
        csv_data = schema.dump(context.data)
        output = io.StringIO()
        save_as_csv(output, schema.get_csv_headers(), csv_data)
        return output

    def to_xlsx(self, context):
        output = io.BytesIO()
        writer = pd.ExcelWriter(
            output, engine="xlsxwriter"
        )  # https://stackoverflow.com/a/28065603
        csv_output = self._as_csv(context)
        csv_output.seek(0)
        pd.read_csv(csv_output, sep=";").to_excel(writer, index=False)
        writer.save()
        return output.getvalue()


class ZipHandler(BaseHandler):
    def deserialize(self, stream, content_type, content_length):
        # Todo - to be implemented. For now do nothing
        return stream

    def serialize(self, media, content_type):
        return media
