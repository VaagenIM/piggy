from html import unescape

from flask import Blueprint, request, jsonify

from piggy.piggybank import PIGGYMAP, get_piggymap_segment_from_path
from piggy.search import build_search_index
from piggy.thumbnails import create_thumbnail
from piggy.utils import serve_pil_image, lru_cache_wrapper, process_json_for_api

api_routes = Blueprint("api", __name__, url_prefix="/api")


@api_routes.route("/generate_thumbnail/<string:text>")
def generate_thumbnail(text: str, request=request):
    """Generate a deterministic, readable fallback thumbnail."""
    text = unescape(text).strip()

    raw_bg_color = request.args.get(
        "bg_color",
        "",
    )

    raw_text_color = request.args.get(
        "text_color",
        "",
    )

    width = request.args.get(
        "width",
        640,
    )

    height = request.args.get(
        "height",
        200,
    )

    # `c` is simply a stable visual seed.
    style_seed = (
        request.args.get("c", "")
        or text
    )

    def sanitize_hex(
        value: str,
    ) -> str | None:
        """
        Return a clean `rrggbb` hex string, or `None` when nothing
        usable was supplied -- `create_thumbnail` treats `None` as
        "no override, choose a curated palette", so this must never
        invent a fallback colour of its own.
        """
        value = (
            (value or "")
            .strip()
            .lstrip("#")
            .lower()
        )

        # Allow shorthand such as #fff.
        if len(value) == 3:
            value = "".join(
                char * 2
                for char in value
            )

        if len(value) != 6:
            return None

        try:
            int(value, 16)

        except ValueError:
            return None

        return value

    def sanitize_dimension(
        value,
        default: int,
        minimum: int,
        maximum: int,
    ) -> int:
        try:
            value = int(value)

        except (
            TypeError,
            ValueError,
        ):
            value = default

        return max(
            minimum,
            min(
                value,
                maximum,
            ),
        )

    bg_color = sanitize_hex(raw_bg_color)
    text_color = sanitize_hex(raw_text_color)

    # Your automatic media route explicitly asks for 1024x512.
    # The old max of 1000 silently reduced that to 1000x512.
    width = sanitize_dimension(
        width,
        default=500,
        minimum=128,
        maximum=2048,
    )

    height = sanitize_dimension(
        height,
        default=200,
        minimum=64,
        maximum=2048,
    )

    # Prevent absurd fallback URLs from becoming giant title blocks.
    thumbnail_text = text[:50]

    if len(thumbnail_text) < len(text):
        thumbnail_text = (
            thumbnail_text.rstrip()
            + "..."
        )

    img = create_thumbnail(
        thumbnail_text,
        bg_color=bg_color,
        text_color=text_color,
        size=(
            width,
            height,
        ),
        seed=style_seed,
    )

    return serve_pil_image(img)


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
