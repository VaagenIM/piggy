from hashlib import md5
from html import unescape

from flask import Blueprint, request, jsonify

from piggy import ASSIGNMENT_ROUTE
from piggy.piggybank import PIGGYMAP, get_piggymap_segment_from_path
from piggy.thumbnails import create_thumbnail
from piggy.utils import serve_pil_image, lru_cache_wrapper, process_json_for_api

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


@api_routes.route("/<path:route>")
@lru_cache_wrapper
def api_route_json(route):
    """Return a JSON of metadata and segment for the given route."""
    # Retrieve metadata and segment using the route
    meta, segment = get_piggymap_segment_from_path(route, PIGGYMAP)
    response_data = {"meta": meta, "segment": segment}
    return jsonify(process_json_for_api(response_data))


@api_routes.route("/")
@lru_cache_wrapper
def api_piggymap():
    """Return the entire piggymap."""
    return jsonify(process_json_for_api(PIGGYMAP))


@api_routes.route("/search-data")
@lru_cache_wrapper
def api_search_index():
    """Return a flat list of all assignments for use with lunr search."""
    results = []

    def _get_body_snippet(file_path: str, max_chars: int = 400) -> str:
        """Read the markdown body (after frontmatter), strip markup, return a short snippet."""
        import re as _re

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return ""
        # Skip frontmatter block
        body_lines = []
        in_front = False
        i = 0
        if lines and lines[0].strip() == "---":
            in_front = True
            i = 1
        while i < len(lines):
            if in_front:
                if lines[i].strip() == "---":
                    in_front = False
                i += 1
                continue
            body_lines.append(lines[i])
            i += 1
        body = "".join(body_lines)
        # Strip markdown: callouts/blockquotes, headings, bold/italic, links, images, code blocks, html tags
        body = _re.sub(r"```.*?```", " ", body, flags=_re.DOTALL)
        body = _re.sub(r"`[^`]+`", " ", body)
        body = _re.sub(r"^>.*$", "", body, flags=_re.MULTILINE)
        body = _re.sub(r"!\[.*?\]\(.*?\)", " ", body)
        body = _re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
        body = _re.sub(r"<[^>]+>", " ", body)
        body = _re.sub(r"^#{1,6}\s+", "", body, flags=_re.MULTILINE)
        body = _re.sub(r"[*_~`|]+", "", body)
        body = _re.sub(r"\s+", " ", body).strip()
        return body[:max_chars]

    def _walk(node: dict, path_parts: list):
        for key, value in node.items():
            if key == "meta":
                continue
            if not isinstance(value, dict):
                continue
            # Leaf node: has a "path" key (it's an assignment file entry)
            if "path" in value:
                meta = value.get("meta", {})
                url_path = "/".join(path_parts + [key])
                file_path = value.get("path", "")
                content = _get_body_snippet(str(file_path)) if file_path else ""
                results.append(
                    {
                        "id": url_path,
                        "title": value.get("level_name") or value.get("heading") or key,
                        "description": meta.get("description", ""),
                        "tags": meta.get("tags", ""),
                        "content": content,
                        "url": f"/{ASSIGNMENT_ROUTE}/{url_path}",
                    }
                )
            else:
                data = value.get("data", {k: v for k, v in value.items() if k != "meta"})
                _walk(data, path_parts + [key])

    _walk(dict(PIGGYMAP), [])
    return jsonify(results)
