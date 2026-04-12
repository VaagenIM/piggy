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

    # Text, Background combinations  (text_color, bg_color)
    color_palettes = [
        ("ffffff", "85144b"),
        ("001f3f", "39cccc"),
        ("ff851b", "001f3f"),
        ("2ecc40", "001f3f"),
        ("39cccc", "001f3f"),
        ("7fdbff", "85144b"),
        ("f012be", "111111"),
        ("ffdc00", "111111"),
        ("001f3f", "ff4136"),
        ("ffffff", "111111"),
        ("111111", "ffffff"),
        ("ff4136", "111111"),
        ("2ecc40", "111111"),
        ("ff4136", "85144b"),
        # Earthy / warm
        ("fefae0", "3a5a40"),
        ("f4f1de", "e07a5f"),
        ("264653", "e9c46a"),
        ("f2e9e4", "6b4226"),
        # Cool / modern
        ("caf0f8", "023e8a"),
        ("e0fbfc", "293241"),
        ("f8f9fa", "495057"),
        ("ffffff", "6c63ff"),
        # Vivid / bold
        ("1a1a2e", "e94560"),
        ("fca311", "14213d"),
        ("edf2f4", "d90429"),
        ("f72585", "3a0ca3"),
        ("4cc9f0", "560bad"),
        ("80ffdb", "2b2d42"),
    ]

    if gibberish and not bg_color and not text_color:
        # Hash both gibberish and the text so each title gets a unique palette
        seed = int(md5((gibberish + text).encode()).hexdigest(), 16)
        text_color, bg_color = color_palettes[seed % len(color_palettes)]

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
