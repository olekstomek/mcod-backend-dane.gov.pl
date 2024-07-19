from django.conf import settings
from hypereditor.blocks import register, register_chooser
from hypereditor.blocks.base import Block
from hypereditor.blocks.chooser import Chooser
from wagtail.embeds.format import embed_to_frontend_html
from wagtail.images import get_image_model

Image = get_image_model()


@register("video")
class Video(Block):
    title = "Video"
    description = "Embedded video (like YouTube)"
    schema = {
        "fields": [
            {
                "type": "input",
                "inputType": "text",
                "label": "Video URL",
                "model": "video_url",
            },
            {
                "type": "input",
                "inputType": "text",
                "label": "Caption Text",
                "model": "video_caption",
            },
        ]
    }

    def get_context(self, parent_context=None):
        video_url = self.obj["settings"].get("video_url", "")
        self.obj["settings"]["player_html"] = embed_to_frontend_html(video_url)
        context = super().get_context(parent_context=parent_context)

        return context


@register_chooser("images")
class ImageChooser(Chooser):
    queryset = Image.objects.filter()
    search_fields = ["title"]

    def _media_url(self, path):
        return "%s%s" % (settings.CMS_URL, path)

    def serialize(self, img):
        try:
            rendition = img.get_rendition("original")
        except Exception:
            rendition = img.renditions.first()

        _image_url = "%s%s" % (settings.CMS_URL, rendition.url) if rendition else ""

        if isinstance(img, Image):
            return {
                "id": img.id,
                "title": img.title,
                "url": _image_url,
            }
        else:
            return img
