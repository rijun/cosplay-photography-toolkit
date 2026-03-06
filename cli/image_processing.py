import io
import pathlib

from PIL import Image, ImageOps

THUMB_WIDTH = 600
MEDIUM_WIDTH = 1600


def make_variant(image_path: pathlib.Path, max_width: int) -> io.BytesIO:
    with Image.open(image_path) as img:
        # img = ImageOps.exif_transpose(img)  # honor rotation from camera EXIF
        img = img.convert("RGB")  # handles PNG/TIFF with alpha channel

        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="webp", quality=82)
        buf.seek(0)
        return buf
