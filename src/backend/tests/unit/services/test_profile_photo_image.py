from io import BytesIO

import pytest
from PIL import Image

from app.core.error import AuthException
from app.services.profile_photo import normalize_image


def test_image_orientation_is_applied_before_metadata_removal():
    """Scenario: phone orientation is retained visually while EXIF is removed."""
    # Given: a landscape photo that EXIF says to rotate 90 degrees.
    source = Image.new("RGB", (80, 40), "blue")
    exif = Image.Exif()
    exif[274] = 6
    buffer = BytesIO()
    source.save(buffer, "JPEG", exif=exif)
    # When: normalization decodes and re-encodes it.
    with Image.open(BytesIO(normalize_image(buffer.getvalue()))) as result:
        # Then: orientation is baked into pixels and metadata is absent.
        assert result.size == (40, 80)
        assert not result.getexif()


def test_image_pixel_limit_rejects_compressed_oversize():
    """Scenario: small compressed files cannot bypass the decoded-pixel bound."""
    # Given: more than 16 million highly compressible pixels.
    buffer = BytesIO()
    Image.new("1", (4001, 4000)).save(buffer, "PNG")
    # When/Then: rejection occurs before loading all pixel data.
    with pytest.raises(AuthException):
        normalize_image(buffer.getvalue())
