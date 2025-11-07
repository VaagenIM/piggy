from hashlib import md5
from html import unescape

from flask import Blueprint, request

from piggy.thumbnails import create_thumbnail
from piggy.utils import serve_pil_image

api_routes = Blueprint("api", __name__, url_prefix="/api")


@api_routes.route("/generate_thumbnail/<string:text>")
def generate_thumbnail(text: str, request=request):
    """Generate a thumbnail image with the given text and query parameters."""
    text = unescape(text)
    bg_color = request.args.get("bg_color", "")
    text_color = request.args.get("text_color", "")
    width = request.args.get("width", 500)
    height = request.args.get("height", 200)

    # c is a hash of the text to get a color combination
    gibberish = request.args.get("c", "")

    # Text, Background combinations
    color_palettes = [
        ("ffffff", "85144b"),
        ("001f3f", "39cccc"),
        ("ff851b", "001f3f"),
        ("2ecc40", "001f3f"),
        ("39cccc", "001f3f"),
        ("7fdbff", "85144b"),
        ("ff851b", "001f3f"),
        ("f012be", "111111"),
        ("ffdc00", "111111"),
        ("001f3f", "ff4136"),
        ("ffffff", "111111"),
        ("111111", "ffffff"),
        ("ff4136", "111111"),
        ("2ecc40", "111111"),
        ("ff4136", "85144b"),
    ]

    if gibberish and not bg_color and not text_color:
        # use a simple hashing function to get a color combination from the gibberish
        text_color, bg_color = color_palettes[int(md5(gibberish.encode()).hexdigest(), 16) % len(color_palettes)]

    if not bg_color:
        bg_color = "111111"
    if not text_color:
        text_color = "fefefe"

    # sanitize the query parameters, text is max 50ch
    _text = text[:50]
    if len(_text) < len(text):
        _text += "..."
    bg_color = bg_color.lstrip("#")
    text_color = text_color.lstrip("#")
    width = min(int(width), 1000)
    height = min(int(height), 1000)

    # create the thumbnail
    img = create_thumbnail(_text, bg_color, text_color, (width, height)).convert("RGB")
    return serve_pil_image(img)
