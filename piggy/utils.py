import os
import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from bs4 import BeautifulSoup as bs
from flask import send_file, request

from piggy import ALLOWED_URL_CHARS_REGEX, IMG_FMT, MEDIA_ROUTE, ASSIGNMENT_ROUTE
from piggy.models import LANGUAGES
from turtleconverter import generate_static_files


def lru_cache_wrapper(func):
    if os.environ.get("USE_CACHE", "1") == "1":
        return lru_cache()(func)
    return func


def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, "webp", quality=100)
    img_io.seek(0)
    return send_file(img_io, mimetype="image/webp")


@lru_cache_wrapper
def get_supported_languages(assignment_path: Path):
    languages = {
        iso_code: lang
        for iso_code, lang in LANGUAGES.items()
        if (assignment_path.parent / "translations" / iso_code / assignment_path.name).exists()
    }
    return {"": LANGUAGES[""], **languages}


@lru_cache_wrapper
def normalize_path_to_str(path: Path or str, replace_spaces=False, normalize_url=False, remove_ext=False) -> str:
    """Normalize a path to use forward slashes and replace spaces with underscores."""
    path = str(path).replace("\\", "/")
    if replace_spaces:
        path = path.replace(" ", "_")
    if normalize_url:
        path = normalize_url_str(path)
    if remove_ext:
        path = re.sub(r"\.\w+$", "", path)
    return path


@lru_cache_wrapper
def generate_summary_from_mkdocs_html(html_content: str) -> str:
    """
    Generate a summary of the html_content using bs4
    """
    soup = bs(html_content, "html.parser").find("article", class_="md-content__inner")
    summary = soup.text[:197].strip() + "..." if soup else ""
    return summary


@lru_cache_wrapper
def normalize_url_str(text: str) -> str:
    """Removes all special characters from the provided str using the ALLOWED_URL_CHARS_REGEX regex"""
    new_text = "".join(c.group() for c in ALLOWED_URL_CHARS_REGEX.finditer(text))
    return re.sub("_+", "_", new_text)


THEME_PATH = "piggy/static/css/themes"


@lru_cache_wrapper
def get_themes():
    themes = os.listdir(THEME_PATH)

    theme_output = []

    for theme in themes:
        theme_data = get_css_metadata(THEME_PATH + f"/{theme}")

        if theme_data is None:
            continue

        theme_output.append(theme_data)

    return sorted(theme_output, key=lambda d: int(d.get("id", 9999)))


def generate_print_css():
    css_folder = Path(__file__).parent / "static" / "css"
    with (css_folder / "base" / "print.css").open("r", encoding="utf-8") as f:
        css = f.read()

    with (css_folder / "themes" / "light.css").open("r", encoding="utf-8") as f:
        light_css = f.read()
        light_css = re.sub(r'\[\s*data-theme\s*=\s*["\']light["\']\s*\]', ":root" * 3, light_css)

    css = css.replace("/* LIGHT_THEME_PLACEHOLDER */", light_css)

    with (css_folder / "base" / "print_overrides.css").open("w+", encoding="utf-8") as f:
        f.write(css)


# Lightweight state machine to read CSS metadata blocks. Theme CSS stays the
# source of truth for colors, while metadata gives the settings UI richer cards.
class ParserState:
    INIT = 1
    READ = 2


CSS_META_IDENTIFIER = "/* METADATA"
CSS_META_LIST_KEYS = {"tags", "recommended_for", "features"}


@lru_cache_wrapper
def get_css_metadata(path: str):
    css_metadata = {}
    css_path = Path(path)

    if css_path.suffix != ".css":
        return None

    state = ParserState.INIT

    with css_path.open(encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip().lstrip("\ufeff")

            if state == ParserState.INIT:
                if not line:
                    continue

                if line.startswith(CSS_META_IDENTIFIER):
                    state = ParserState.READ
                    continue

                return None

            if line.startswith("*/"):
                break

            if not line or line.startswith("#"):
                continue

            meta_item = line.split(":", 1)
            if len(meta_item) < 2:
                continue

            key = meta_item[0].strip()
            value = parse_css_metadata_value(key, meta_item[1].strip())
            set_css_metadata_value(css_metadata, key, value)

    if state == ParserState.INIT or not css_metadata:
        return None

    css_metadata["path"] = css_path.stem

    return css_metadata


def parse_css_metadata_value(key: str, value: str):
    metadata_key = key.rsplit(".", 1)[-1]

    if metadata_key in CSS_META_LIST_KEYS:
        return [item.strip() for item in value.split(",") if item.strip()]

    if metadata_key == "id" and value.isdigit():
        return int(value)

    normalized_value = value.lower()
    if normalized_value in {"true", "false"}:
        return normalized_value == "true"

    return value


def set_css_metadata_value(metadata: dict, key: str, value):
    parts = [part.strip() for part in key.split(".") if part.strip()]
    if not parts:
        return

    current = metadata
    for part in parts[:-1]:
        if not isinstance(current.get(part), dict):
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value


def process_json_for_api(obj, exclude_keys=None):
    def apply_thumbnail(thumb, current_path):
        """Turn the thumbnail path into an absolute URL"""

        # Best effort guess to generate a thumbnail URL based on the current path and the thumbnail path
        if not thumb:
            thumb = "media/header"
        if not current_path and request:
            current_path = request.path.strip("/")

        if not isinstance(thumb, str):
            return thumb

        if thumb.startswith("/"):
            return thumb

        thumb = thumb.rsplit(".", 1)[0]

        if current_path:
            folder = Path(current_path).parent.as_posix()
            folder = re.sub(r"^[^/]+/", "", folder)
            folder = normalize_path_to_str(folder, replace_spaces=True, normalize_url=True)
            return f"/{MEDIA_ROUTE}/{folder}/{thumb}.{IMG_FMT}"

        return f"/{MEDIA_ROUTE}/{thumb}.{IMG_FMT}"

    def transform(obj, current_path=None):
        if isinstance(obj, dict):
            if "path" in obj:
                current_path = str(obj["path"])

            new_obj = {}

            # We need to iterate through to grab/fix:
            # - URLs for any segments with paths
            # - Thumbnails should be asbolute URLs
            for k, v in obj.items():
                # If we have a path or system path, we can generate a URL
                # If we have a system path with no specified thumbnail, we can use the default path
                if k in ("path", "system_path") and isinstance(v, Path):
                    # Remove the first folder and the extension from the path
                    file_path = v.as_posix()
                    p = re.sub(r"^[^/]+/|(\.\w+)$", "", file_path)
                    p = normalize_path_to_str(p, replace_spaces=True, normalize_url=True)

                    url = f"/{ASSIGNMENT_ROUTE}/{p}"

                    new_obj["file_path"] = file_path
                    new_obj["url"] = url
                    if k == "system_path" and "thumbnail" not in new_obj:
                        new_obj["thumbnail"] = f"/{MEDIA_ROUTE}/{p}/media/header.{IMG_FMT}"
                    continue

                # Special handling for "meta" keys to transform thumbnail paths
                if k == "meta" and isinstance(v, dict):
                    meta = transform(v, current_path)
                    meta["thumbnail"] = apply_thumbnail(meta.get("thumbnail"), current_path)
                    new_obj[k] = meta
                    continue

                if exclude_keys and k in exclude_keys:
                    continue

                if k.startswith("turtletranslate_"):
                    continue

                new_obj[k] = transform(v, current_path)

            return new_obj

        if isinstance(obj, list):
            return [transform(i, current_path) for i in obj]

        return obj

    return transform(obj)


def delete_turtleconverter_stylesheets():
    """No longer used, might as well save a couple bytes."""
    stylesheets_path = Path(__file__).parent / "static" / "turtleconvert" / "stylesheets"
    if stylesheets_path.exists() and stylesheets_path.is_dir():
        for file in stylesheets_path.iterdir():
            if file.is_file():
                file.unlink()
        stylesheets_path.rmdir()


def startup_tasks():
    generate_static_files(static_folder=Path(os.path.dirname(Path(__file__).absolute())) / "static")
    # delete_turtleconverter_stylesheets()
    generate_print_css()
