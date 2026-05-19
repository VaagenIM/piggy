import re

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, request, jsonify

from piggy.utils import lru_cache_wrapper

tts_routes = Blueprint("tts-index", __name__, url_prefix="/tts-index")

AUDIO_BLOCK_SELECTOR = [
    "p", "li", "dt", "dd", "figcaption",
    "td", "th",
    "h1", "h2", "h3", "h4", "h5", "h6"
]

SKIP_SELECTORS = {"script", "style", "pre"}

URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def normalize_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def split_sentences(text):
    if not text:
        return []

    urls = {}

    def replace_url(match):
        key = f"__URL{len(urls)}__"
        urls[key] = match.group(0)
        return key

    protected = URL_PATTERN.sub(replace_url, text)

    pattern = r'[^.!?]+(?:[.!?]+["\')\]]*)?|\S+'
    matches = re.finditer(pattern, protected)

    results = []
    for m in matches:
        s = normalize_text(m.group(0))
        if not s:
            continue

        for k, v in urls.items():
            s = s.replace(k, v)

        results.append(s)

    return results


def should_skip(element):
    return element.name in SKIP_SELECTORS


def extract_text_preserve(tag):
    return normalize_text(" ".join(tag.stripped_strings))


def get_kind(tag):
    return "header" if tag.name and tag.name.startswith("h") else "text"


def build_block(tag, block_index):
    text = extract_text_preserve(tag)
    if not text:
        return None

    sentences = split_sentences(text)
    if not sentences:
        return None

    kind = "header" if tag.name and tag.name.startswith("h") else "text"

    return {
        "id": f"{block_index:03d}",
        "kind": kind,
        "items": [
            {
                "text": sentence,
                "index": i,
            }
            for i, sentence in enumerate(sentences)
        ]
    }


def extract_inventory(html):
    soup = BeautifulSoup(html, "html.parser")

    markdown_content = soup.select_one("main .md-content")
    if not markdown_content:
        return []

    result = []
    block_index = 0

    # Page header first (if present)
    page_header = soup.select_one(".assignment-page-header")
    if page_header:
        block = build_block(page_header, block_index)
        if block:
            # force it to always be header
            block["kind"] = "header"
            result.append(block)
            block_index += 1

    # Main content blocks
    for tag in markdown_content.find_all(AUDIO_BLOCK_SELECTOR):
        if should_skip(tag):
            continue

        block = build_block(tag, block_index)
        if not block:
            continue

        result.append(block)
        block_index += 1

    return result


@tts_routes.route("/<path:page_path>")
@lru_cache_wrapper
def tts_index(page_path):
    url = f"{request.url_root}/main/{page_path}"

    response = requests.get(url)

    inventory = extract_inventory(response.text)

    return jsonify(inventory)
