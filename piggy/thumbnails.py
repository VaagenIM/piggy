import textwrap
from pathlib import Path

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

from piggy.utils import lru_cache_wrapper


# TODO: this is a mess.


@lru_cache_wrapper
def create_thumbnail(
    title: str, bg_color: str = "111111", text_color: str = "fefefe", size: tuple[int, int] = (700, 300)
) -> PIL.Image:
    """Returns the image data for a thumbnail of the given image."""
    im = PIL.Image.new("RGB", size, "#" + bg_color)
    box = (0, 0, size[0], size[1])
    draw = PIL.ImageDraw.Draw(im)

    x_margin = 40
    y_margin = 70

    # Plays better with the text overlay
    y_offset = 10

    text = textwrap.fill(title, width=30)
    font_size = 180
    size = None

    # Get the font path relative to this file
    font_path = Path(__file__).parent / "resources/fonts/Lato-Bold.ttf"
    font = PIL.ImageFont.truetype(font_path.as_posix(), font_size)
    recursions = 0
    while (
        (size is None or size[2] > box[2] - x_margin or size[3] > box[3] - y_margin)
        and font_size > 0
        and recursions < 50
    ):
        font = font.font_variant(size=font_size)
        size = draw.multiline_textbbox((0, 0), text, font=font, align="center")
        font_size -= 5
        recursions += 1

    box = (box[2] / 2, box[3] / 2 - y_offset)

    draw.multiline_text(box, text, font=font, fill="#" + text_color, align="center", anchor="mm")

    return im
