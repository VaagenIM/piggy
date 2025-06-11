import os
import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from bs4 import BeautifulSoup as bs
from flask import send_file

from piggy import ALLOWED_URL_CHARS_REGEX
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
