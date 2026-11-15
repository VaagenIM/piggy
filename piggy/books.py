"""Validated book navigation built from topic metadata and the assignment map."""

import re
from collections.abc import Mapping
from html import unescape
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import quote


class BookValidationError(ValueError):
    """A book cannot be published with its current metadata or page targets."""


def _text(value, context):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise BookValidationError(f"{context}: expected a nonempty, trimmed string")
    return value


def _page(value, context):
    value = _text(value, context)
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or any(part in ("", ".", "..") for part in value.split("/"))
        or any(char in value for char in "\\:%?#")
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
        or path.suffix != ".md"
    ):
        raise BookValidationError(f"{context}: expected a safe root-relative Markdown filename")
    return value


def validate_book_definition(book, context="book"):
    """Validate metadata and return a fresh definition with normalized primitives."""
    if not isinstance(book, Mapping) or set(book) != {"title", "contents", "chapters"}:
        raise BookValidationError(f"{context}: expected exactly title, contents and chapters")
    title = _text(book["title"], f"{context}.title")
    contents = _page(book["contents"], f"{context}.contents")
    if not isinstance(book["chapters"], (list, tuple)) or not book["chapters"]:
        raise BookValidationError(f"{context}.chapters: expected a nonempty ordered list")
    chapters = []
    seen = set()
    for number, chapter in enumerate(book["chapters"], 1):
        location = f"{context}.chapters[{number}]"
        if not isinstance(chapter, Mapping) or set(chapter) != {"title", "page", "anchor"}:
            raise BookValidationError(f"{location}: expected exactly title, page and anchor")
        chapter_title = _text(chapter["title"], f"{location}.title")
        page = _page(chapter["page"], f"{location}.page")
        anchor = _text(chapter["anchor"], f"{location}.anchor")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", anchor):
            raise BookValidationError(f"{location}.anchor: expected an explicit safe HTML id (without #)")
        if (page, anchor) in seen:
            raise BookValidationError(f"{location}: duplicate chapter target {page}#{anchor}")
        if page == contents:
            raise BookValidationError(f"{location}: contents must be separate from chapter pages")
        seen.add((page, anchor))
        chapters.append({"title": chapter_title, "page": page, "anchor": anchor})
    return {"title": title, "contents": contents, "chapters": chapters}


class _AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.ids.extend(value for key, value in attrs if key == "id")


def _explicit_anchors(path):
    lines = []
    fence = None
    for line in path.read_text(encoding="utf-8").splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None and not line.startswith(("    ", "\t")):
            lines.append(line)
    parser = _AnchorParser()
    parser.feed("\n".join(lines))
    return parser.ids


def _translated_titles(translation_meta):
    if not isinstance(translation_meta, Mapping):
        return {}
    return {
        language: unescape(metadata["title"])
        for language, metadata in translation_meta.items()
        if isinstance(metadata, Mapping)
        and isinstance(metadata.get("title"), str)
        and metadata["title"].strip()
    }


def build_book_index(piggymap: Mapping, root: Path, *, route="main", check_anchors=True):
    """Return a root-relative navigation model for every member page in each book."""
    root = Path(root).resolve()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", route):
        raise BookValidationError("book route must be a single safe URL segment")
    pages = {}
    definitions = []

    def walk(segment, keys=(), public=True):
        for key, node in segment.items():
            if not isinstance(node, Mapping):
                continue
            current = (*keys, key)
            meta = node.get("meta", {})
            visible = public and meta.get("visibility", "public") == "public"
            if "book" in meta:
                context = "/".join(current) + "/meta.json:book"
                if len(current) != 4:
                    raise BookValidationError(f"{context}: book metadata belongs to a topic")
                if not visible:
                    raise BookValidationError(f"{context}: book owner must be public")
                definitions.append((context, validate_book_definition(meta["book"], context)))
            if "path" in node:
                try:
                    relative = Path(node["path"]).resolve().relative_to(root).as_posix()
                except ValueError:
                    continue
                url = "/" + route + "/" + "/".join(quote(part, safe="-._~") for part in current)
                translation_meta = node.get("translation_meta", {})
                pages[relative] = {
                    "url": url,
                    "public": visible,
                    "translations": tuple(translation_meta) if isinstance(translation_meta, Mapping) else (),
                    "titles": _translated_titles(translation_meta),
                }
            if "data" in node:
                walk(node["data"], current, visible)

    walk(piggymap)
    index = {}
    anchors = {}

    def language_urls(page, anchor=""):
        fragment = f"#{anchor}" if anchor else ""
        return {
            language: f"{pages[page]['url']}/lang/{quote(language, safe='-._~')}{fragment}"
            for language in pages[page]["translations"]
            if isinstance(language, str) and re.fullmatch(r"[A-Za-z0-9_-]+", language)
        }

    for context, definition in definitions:
        contents_page = definition["contents"]
        members = {contents_page, *(chapter["page"] for chapter in definition["chapters"])}
        for page in members:
            target = (root / page).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                raise BookValidationError(f"{context}: missing or unsafe page {page}")
            if page not in pages or not pages[page]["public"]:
                raise BookValidationError(f"{context}: page is not a public assignment: {page}")
            if page in index:
                raise BookValidationError(f"{context}: page already belongs to another book: {page}")

        contents_titles = pages[contents_page]["titles"]
        contents = {
            "page": contents_page,
            "url": pages[contents_page]["url"],
            "language_urls": language_urls(contents_page),
            "language_labels": contents_titles,
            "label": "Innhold",
            "anchor": "",
        }
        chapters = []
        for number, chapter in enumerate(definition["chapters"], 1):
            page, anchor = chapter["page"], chapter["anchor"]
            if check_anchors:
                if page not in anchors:
                    anchors[page] = _explicit_anchors(root / page)
                if anchors[page].count(anchor) != 1:
                    raise BookValidationError(f'{context}: expected exactly one explicit <a id="{anchor}"> in {page}')
            translated_titles = pages[page]["titles"]
            chapters.append(
                {
                    **chapter,
                    "number": number,
                    "label": f"Kapittel {number} – {chapter['title']}",
                    "language_labels": {lang: f"{number}. {title}" for lang, title in translated_titles.items()},
                    "url": f"{pages[page]['url']}#{anchor}",
                    "language_urls": language_urls(page, anchor),
                }
            )
        entries = [contents, *chapters]
        for page in members:
            current_indexes = [i for i, entry in enumerate(entries) if entry["page"] == page]
            initial = current_indexes[0]
            index[page] = {
                "title": definition["title"],
                "language_titles": contents_titles,
                "contents": contents,
                "chapters": chapters,
                "entries": entries,
                "current_indexes": current_indexes,
                "current_index": initial,
                "current": entries[initial],
                "previous": entries[initial - 1] if initial else None,
                "next": entries[initial + 1] if initial + 1 < len(entries) else None,
            }
    return index
