"""Validated book navigation, independent of Flask and Markdown converters.

The index is derived from topic metadata and the published assignment map. It
never invents routes from filenames or copies page content. Invalid definitions
raise BookValidationError during startup/static builds instead of hiding a book.
"""

import re
from collections.abc import Mapping
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
    """Validate the metadata shape; return a fresh normalized definition.

    Full publication checks (public pages, ownership, files, explicit anchors)
    belong to build_book_index. Only JSON-compatible primitives are returned.
    """
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
    # Fenced examples must not count as real navigation targets.
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


def build_book_index(piggymap: Mapping, root: Path, *, route="main", check_anchors=True):
    """Return root-relative page -> navigation model for every book member.

    Paths in metadata must resolve to existing public assignment nodes in
    piggymap. Folder visibility is inherited, including on older app versions.
    URLs use actual map keys, preserving existing public routes/shortlinks.
    Chapters may share a file within one book, but pages cannot belong to two
    books. Explicit <a id="…"> targets are checked by default.
    """
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
                pages[relative] = {"url": url, "public": visible}
            if "data" in node:
                walk(node["data"], current, visible)

    walk(piggymap)
    index = {}
    anchors = {}
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
        contents = {"page": contents_page, "url": pages[contents_page]["url"], "label": "Innhold", "anchor": ""}
        chapters = []
        for number, chapter in enumerate(definition["chapters"], 1):
            page, anchor = chapter["page"], chapter["anchor"]
            if check_anchors:
                if page not in anchors:
                    anchors[page] = _explicit_anchors(root / page)
                if anchors[page].count(anchor) != 1:
                    raise BookValidationError(f'{context}: expected exactly one explicit <a id="{anchor}"> in {page}')
            chapters.append(
                {
                    **chapter,
                    "number": number,
                    "label": f"Kapittel {number} – {chapter['title']}",
                    "url": f"{pages[page]['url']}#{anchor}",
                }
            )
        entries = [contents, *chapters]
        for page in members:
            current_indexes = [i for i, entry in enumerate(entries) if entry["page"] == page]
            initial = current_indexes[0]
            index[page] = {
                "title": definition["title"],
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
