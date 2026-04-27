import os
import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from bs4 import BeautifulSoup as bs
from flask import send_file, request

from piggy import ALLOWED_URL_CHARS_REGEX, IMG_FMT, MEDIA_ROUTE, ASSIGNMENT_ROUTE
from piggy.models import LANGUAGES


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

    return sorted(theme_output, key=lambda d: int(d["id"]))


# quick and dirty state_machine to read CSS metadata
class ParserState:
    INIT = 1
    READ = 2


CSS_META_IDENTIFIER = "/* METADATA"


@lru_cache_wrapper
def get_css_metadata(path: str):
    css_metadata = {}
    css_path = Path(path)

    if css_path.suffix != ".css":
        return None

    valid = True
    state = ParserState.INIT

    with css_path.open() as file:
        while valid:
            line = file.readline()

            match state:
                case ParserState.INIT:
                    if str(line).startswith(CSS_META_IDENTIFIER):
                        state = ParserState.READ
                    else:
                        valid = False
                case ParserState.READ:
                    meta_item = line.split(":", 1)

                    if len(meta_item) < 2:
                        valid = False
                    else:
                        css_metadata[meta_item[0].strip()] = meta_item[1].strip()

    css_metadata["path"] = css_path.stem

    return css_metadata


def process_json_for_api(obj):
    def apply_thumbnail(thumb, current_path):
        """Turn the thumbnail path into an absolute URL"""

        # Best effort guess to generate a thumbnail URL based on the current path and the thumbnail path
        if not thumb:
            thumb = "media/header"
        if not current_path and request:
            current_path = request.path[len("/api/") :]

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

                if k == "translation_meta" and isinstance(v, dict):
                    meta_block = {}

                    for lang, lang_meta in v.items():
                        if isinstance(lang_meta, dict):
                            lang_meta = transform(lang_meta, current_path)
                            lang_meta["thumbnail"] = apply_thumbnail(lang_meta.get("thumbnail"), current_path)

                        meta_block[lang] = lang_meta

                    new_obj[k] = meta_block
                    continue

                if k.startswith("turtletranslate_"):
                    continue

                new_obj[k] = transform(v, current_path)

            return new_obj

        if isinstance(obj, list):
            return [transform(i, current_path) for i in obj]

        return obj

    return transform(obj)
