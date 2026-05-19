from hashlib import md5
from html import unescape
from pathlib import Path

from flask import Blueprint, request, jsonify

from piggy import ASSIGNMENT_ROUTE, AssignmentTemplate
from piggy.caching import _mdfile_to_sections_with_retry
from piggy.exceptions import PiggyHTTPException
from piggy.models import LANGUAGES
from piggy.piggybank import PIGGYMAP, get_piggymap_segment_from_path
from piggy.reader_audio import build_reader_audio_map
from piggy.search import build_search_index
from piggy.thumbnails import create_thumbnail
from piggy.utils import serve_pil_image, lru_cache_wrapper, process_json_for_api, normalize_path_to_str

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


@api_routes.route("/get-audio-map/<path:route>", strict_slashes=False)
def api_reader_audio_map(route):
    """Return the reader audio IDs and text for an assignment."""
    lang = request.args.get("lang", "").strip()
    route, lang = normalize_audio_map_route(route, lang)
    return jsonify(get_reader_audio_map_from_route(route, lang))


def normalize_audio_map_route(route: str, lang: str = "") -> tuple[str, str]:
    route = normalize_path_to_str(route.strip("/"), replace_spaces=True)

    if route.startswith(f"{ASSIGNMENT_ROUTE}/"):
        route = route.removeprefix(f"{ASSIGNMENT_ROUTE}/")

    parts = [part for part in route.split("/") if part]
    if len(parts) >= 2 and parts[-2] == "lang":
        lang = lang or parts[-1]
        parts = parts[:-2]

    return "/".join(parts), lang


@lru_cache_wrapper
def get_reader_audio_map_from_route(route: str, lang: str = ""):
    if lang and lang not in LANGUAGES:
        raise PiggyHTTPException("Audio map not found", status_code=404)

    route = normalize_path_to_str(route, replace_spaces=True)
    if len([part for part in route.split("/") if part]) != AssignmentTemplate.ASSIGNMENT.index:
        raise PiggyHTTPException("Audio map not found", status_code=404)

    _, segment = get_piggymap_segment_from_path(route, PIGGYMAP)
    assignment_path = segment.get("path", Path())

    if not assignment_path:
        raise PiggyHTTPException("Audio map not found", status_code=404)

    render_path = assignment_path
    if lang:
        render_path = assignment_path.parent / "translations" / lang / assignment_path.name
        if not render_path.exists():
            raise PiggyHTTPException("Audio map not found", status_code=404)

    sections = _mdfile_to_sections_with_retry(render_path)
    level = segment.get("level", 0)

    return build_reader_audio_map(
        sections.get("body", ""),
        sections.get("heading", ""),
        level,
    )


@api_routes.route("/<path:route>")
@lru_cache_wrapper
def api_route_json(route):
    """Return a JSON of metadata and segment for the given route."""
    # Retrieve metadata and segment using the route
    meta, segment = get_piggymap_segment_from_path(route, PIGGYMAP)
    response_data = {
        **process_json_for_api({"meta": meta}),
        "segment": process_json_for_api(segment, exclude_keys={"translation_meta"}),
    }
    return jsonify(response_data)


@api_routes.route("/")
@lru_cache_wrapper
def api_piggymap():
    """Return the entire piggymap."""
    return jsonify(process_json_for_api(PIGGYMAP))


@api_routes.route("/search-data")
@lru_cache_wrapper
def api_search_index():
    """Return a flat list of all assignments for use with lunr search."""
    return jsonify(build_search_index(PIGGYMAP))
