from flask import Blueprint, request
from piggy.thumbnails import create_thumbnail
from piggy.utils import serve_pil_image

api_routes = Blueprint("api", __name__, url_prefix="/api")


@api_routes.route("/generate_thumbnail/<string:text>")
def generate_thumbnail(text: str):
    """
    Generate a thumbnail from the given heading.

    :param heading: The heading to generate a thumbnail for
    :return: A thumbnail image
    """
    # get query parameters from the request
    bg_color = request.args.get("bg_color", "")
    text_color = request.args.get("text_color", "")
    width = request.args.get("width", 500)
    height = request.args.get("height", 200)

    # c is a hash of the text to get a color combination
    gibberish = request.args.get("c", "")

    # Text, Background combinations
    color_palettes = [
        ("ffffff", "85144b"),
        ("aaaaaa", "000000"),
        ("001f3f", "39cccc"),
        ("ff851b", "001f3f"),
        ("2ecc40", "001f3f"),
        ("39cccc", "001f3f"),
        ("7fdbff", "85144b"),
        ("ff851b", "001f3f"),
    ]

    if gibberish and not bg_color and not text_color:
        # use a simple hashing function to get a color combination from the gibberish
        text_color, bg_color = color_palettes[hash(gibberish) % len(color_palettes)]

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
