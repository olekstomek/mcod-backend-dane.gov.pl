"""Validation helpers for image data URIs.

The module decodes data URI payloads, enforces size and MIME type constraints,
and verifies declared MIME types using libmagic.
"""

import base64
import logging
from dataclasses import dataclass
from typing import Final, Mapping, Optional, Tuple
from urllib.parse import unquote_to_bytes

import magic
from django.conf import settings

logger = logging.getLogger("mcod")


INVALID_BASE64: Final[str] = "invalid_base64"
INVALID_IMAGE: Final[str] = "invalid_image"
INVALID_MIME_TYPE: Final[str] = "invalid_mime_type"
MIME_TYPE_MISMATCH: Final[str] = "mime_type_mismatch"
TOO_LONG: Final[str] = "too_long"

SAFE_IMAGE_CONTENT_TYPE = ["gif", "jpeg", "png", "webp"]
IMAGE_EXTENSION_BY_MIME_TYPE: Final[Mapping[str, str]] = {
    f"{family}/{content_type}": f".{extensions[0]}"
    for family, content_type, extensions, _ in settings.SUPPORTED_CONTENT_TYPES
    if family == "image" and content_type in SAFE_IMAGE_CONTENT_TYPE
}


class ImageValidationError(ValueError):
    """Validation failure carrying a stable error code for caller-specific mapping."""


@dataclass(frozen=True)
class ValidatedImage:
    """Validated image bytes with the canonical MIME type detected from content."""

    decoded_data: bytes
    mime_type: str

    @property
    def extension(self) -> str:
        """Return the storage extension for the verified MIME type."""
        return IMAGE_EXTENSION_BY_MIME_TYPE[self.mime_type]


def parse_base64_image_data_uri(url: str) -> Tuple[bytes, str]:
    """based on DataHandler from urllib.requests
    data URLs as specified in RFC 2397.

    ignores POSTed data

    syntax:
    dataurl   := "data:" [ mediatype ] [ ";base64" ] "," data
    mediatype := [ type "/" subtype ] *( ";" parameter )
    data      := *urlchar
    parameter := attribute "=" value
    """

    try:
        scheme, data = url.split(":", 1)
        mediatype, data = data.split(",", 1)
    except ValueError as exc:
        logger.exception("Invalid data URI")
        raise ImageValidationError(INVALID_MIME_TYPE) from exc

    # even base64 encoded data URLs might be quoted so unquote in any case:
    data = unquote_to_bytes(data)
    if mediatype.endswith(";base64"):
        try:
            data = base64.decodebytes(data)
        except Exception as exc:
            logger.exception("Base64 decode failed")
            raise ImageValidationError(INVALID_BASE64) from exc
        mediatype = mediatype[:-7]

    if not mediatype:
        logger.exception("mediatype not recognized")
        raise ImageValidationError(INVALID_MIME_TYPE)

    return data, mediatype.lower()


def detect_mime_type_using_magic(decoded_data: bytes) -> str:
    """Detect the MIME type of decoded data using libmagic.

    Returns the detected MIME type in lowercase. Raises
    ``ImageValidationError`` if detection fails or returns no MIME type.
    """
    try:
        mime_type: Optional[str] = magic.from_buffer(decoded_data, mime=True)
    except magic.MagicException as exc:
        logger.exception("Libmagic failed while validating uploaded image data")
        raise ImageValidationError(INVALID_IMAGE) from exc
    if not mime_type:
        logger.exception("No MIME type detected")
        raise ImageValidationError(INVALID_MIME_TYPE)
    return mime_type.lower()


def validate_image(value: str) -> ValidatedImage:
    """Validate an image data URI against size and MIME type constraints.

    Both the declared MIME type and the type detected by libmagic must be
    allowed and must match.
    """
    max_size = settings.IMAGE_UPLOAD_MAX_SIZE
    decoded_data, declared_mime_type = parse_base64_image_data_uri(value)
    if len(decoded_data) > max_size:
        logger.exception(f"Image upload failed. Size too large: {len(decoded_data)}")
        raise ImageValidationError(TOO_LONG)
    if declared_mime_type not in IMAGE_EXTENSION_BY_MIME_TYPE:
        logger.exception(f"Image upload failed. Invalid mimetype: {declared_mime_type}")
        raise ImageValidationError(INVALID_MIME_TYPE)
    magic_mime_type = detect_mime_type_using_magic(decoded_data)

    if magic_mime_type not in IMAGE_EXTENSION_BY_MIME_TYPE:
        logger.exception(f"Image upload failed. Invalid mimetype: {magic_mime_type}")
        raise ImageValidationError(INVALID_MIME_TYPE)

    if declared_mime_type != magic_mime_type:
        logger.exception(f"Image upload failed. Mimetype mismatch. {declared_mime_type} != {magic_mime_type}")
        raise ImageValidationError(MIME_TYPE_MISMATCH)

    return ValidatedImage(decoded_data=decoded_data, mime_type=magic_mime_type)
