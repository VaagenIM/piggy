import re
from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup as bs
from bs4 import NavigableString, Tag


READER_AUDIO_ALLOWED_SUFFIXES = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".opus": "audio/ogg",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
}
READER_AUDIO_ID_RE = re.compile(r"^(?:s|p|sec)-\d{2,}-\d{4,}$")

AUDIO_BLOCK_TAGS = {"p", "li", "dt", "dd", "figcaption", "td", "th"}
AUDIO_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
AUDIO_CONTAINER_CHILD_TAGS = {"p", "ul", "ol", "table", "pre", "details"}
AUDIO_BLOCK_SKIP_TAGS = {"a", "button", "script", "style", "pre"}
AUDIO_TEXT_SKIP_TAGS = {"button", "script", "style", "pre"}
AUDIO_SKIP_CLASSES = {"highlight", "MathJax", "arithmatex", "md-code__nav", "settings-reader-preview"}
SENTENCE_RE = re.compile(r"[^.!?]+(?:[.!?]+[\"')\]]*)?|\S+")


def normalize_reader_text(text: str) -> str:
    """Normalize rendered reader text the same way the browser reader does."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def format_audio_level(level: Any) -> str:
    """Return the assignment level as a stable two-digit string."""
    try:
        level_number = int(str(level).strip())
    except (TypeError, ValueError):
        digits = re.sub(r"\D+", "", str(level or ""))
        level_number = int(digits) if digits else 0

    return str(max(0, level_number)).zfill(2)


def create_audio_id(kind: str, level: Any, index: int) -> str:
    return f"{kind}-{format_audio_level(level)}-{index:04d}"


def split_reader_sentences(text: str) -> list[str]:
    if not text:
        return []

    return [
        normalized
        for match in SENTENCE_RE.finditer(text)
        if (normalized := normalize_reader_text(match.group(0)))
    ]


@dataclass
class ReaderAudioMapBuilder:
    level: Any
    sentence_counter: int = 0
    paragraph_counter: int = 0
    section_counter: int = 0
    items: list[dict[str, Any]] = field(default_factory=list)
    block_sentence_ids: dict[int, list[str]] = field(default_factory=dict)
    heading_sentence_ids: dict[int, list[str]] = field(default_factory=dict)
    page_heading_sentence_ids: list[str] = field(default_factory=list)

    def add_sentence(self, text: str) -> str:
        self.sentence_counter += 1
        sentence_id = create_audio_id("s", self.level, self.sentence_counter)
        self.items.append(
            {
                "id": sentence_id,
                "kind": "sentence",
                "text": text,
            }
        )
        return sentence_id

    def add_paragraph(self, text: str, sentence_ids: list[str], element: Tag) -> None:
        self.paragraph_counter += 1
        self.block_sentence_ids[id(element)] = sentence_ids
        self.items.append(
            {
                "id": create_audio_id("p", self.level, self.paragraph_counter),
                "kind": "paragraph",
                "text": text,
                "sequence": sentence_ids,
            }
        )

    def add_section(self, text: str, sequence: list[str]) -> None:
        if not sequence:
            return

        self.section_counter += 1
        self.items.append(
            {
                "id": create_audio_id("sec", self.level, self.section_counter),
                "kind": "section",
                "text": text,
                "sequence": sequence,
            }
        )

    def add_page_heading(self, text: str) -> None:
        self.page_heading_sentence_ids = [
            self.add_sentence(sentence) for sentence in split_reader_sentences(text)
        ]

    def add_heading(self, heading: Tag) -> None:
        heading_text = get_element_audio_text(heading)
        self.heading_sentence_ids[id(heading)] = [
            self.add_sentence(sentence) for sentence in split_reader_sentences(heading_text)
        ]

    def add_block(self, block: Tag) -> None:
        block_text = get_element_audio_text(block)
        if not block_text:
            return

        sentence_texts = split_reader_sentences(block_text) or [block_text]
        sentence_ids = [self.add_sentence(sentence) for sentence in sentence_texts]
        self.add_paragraph(block_text, sentence_ids, block)


def build_reader_audio_inventory(body_html: str, heading: str, level: Any) -> dict[str, Any]:
    """
    Build the reader audio inventory from rendered assignment HTML.

    The browser reader uses the same ID format and traversal order, so this inventory
    can be used both for recording/generation and as a debugging reference.
    """
    soup = bs(body_html or "", "html.parser")
    markdown_content = get_markdown_content(soup)
    builder = ReaderAudioMapBuilder(level=level)

    builder.add_page_heading(normalize_reader_text(heading))

    if markdown_content:
        for element in get_audio_targets(markdown_content):
            if element.name in AUDIO_HEADING_TAGS:
                builder.add_heading(element)
            elif is_readable_audio_block(element):
                builder.add_block(element)

        for heading_element in markdown_content.find_all(AUDIO_HEADING_TAGS):
            if id(heading_element) not in builder.heading_sentence_ids:
                builder.add_heading(heading_element)

        builder.add_section(
            normalize_reader_text(heading),
            [*builder.page_heading_sentence_ids, *collect_sentence_ids(markdown_content, builder)],
        )

        for heading_element in markdown_content.find_all(AUDIO_HEADING_TAGS):
            heading_text = get_element_audio_text(heading_element)
            sequence = [
                *builder.heading_sentence_ids.get(id(heading_element), []),
                *get_section_sentence_ids(heading_element, builder),
            ]
            builder.add_section(heading_text, sequence)

    return {
        "level": format_audio_level(level),
        "items": builder.items,
    }


def build_reader_audio_map(body_html: str, heading: str, level: Any) -> list[dict[str, Any]]:
    """Return the compact public audio map used by `/api/get-audio-map/...`."""
    inventory = build_reader_audio_inventory(body_html, heading, level)
    return compact_reader_audio_items(inventory["items"])


def compact_reader_audio_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []

    for item in items:
        if item.get("kind") == "sentence":
            output.append(
                {
                    "id": item["id"],
                    "text": item.get("text", ""),
                }
            )
            continue

        output.append(
            {
                "id": item["id"],
                "texts": list(item.get("sequence", [])),
            }
        )

    return output


def get_markdown_content(soup: bs) -> Tag | None:
    for content in soup.select("main .md-content, .md-content"):
        if "settings-reader-preview" not in content.get("class", []):
            return content

    return soup if isinstance(soup, Tag) else None


def get_audio_targets(root: Tag) -> list[Tag]:
    target_tags = sorted(AUDIO_BLOCK_TAGS | AUDIO_HEADING_TAGS)
    return [
        element
        for element in root.find_all(target_tags)
        if (
            is_readable_audio_heading(element)
            if element.name in AUDIO_HEADING_TAGS
            else is_readable_audio_block(element)
        )
    ]


def is_readable_audio_heading(element: Tag) -> bool:
    return bool(
        isinstance(element, Tag)
        and element.name in AUDIO_HEADING_TAGS
        and normalize_reader_text(get_element_audio_text(element))
        and not has_skipped_ancestor(element)
    )


def is_readable_audio_block(element: Tag) -> bool:
    if not isinstance(element, Tag):
        return False
    if element.name not in AUDIO_BLOCK_TAGS:
        return False
    if not normalize_reader_text(get_element_audio_text(element)):
        return False
    if has_skipped_ancestor(element):
        return False

    for child in element.find_all(recursive=False):
        if child.name in AUDIO_CONTAINER_CHILD_TAGS:
            return False
        if has_any_class(child, {"highlight"}):
            return False

    return True


def get_element_audio_text(element: Tag) -> str:
    chunks = []

    for descendant in element.descendants:
        if not isinstance(descendant, NavigableString):
            continue
        if has_skipped_ancestor(descendant, stop_at=element, include_links=False):
            continue
        chunks.append(str(descendant))

    return normalize_reader_text("".join(chunks))


def has_skipped_ancestor(
    node: Tag | NavigableString,
    stop_at: Tag | None = None,
    include_links: bool = True,
) -> bool:
    current = node if isinstance(node, Tag) else node.parent

    while isinstance(current, Tag):
        if current is stop_at:
            return False
        if is_skipped_element(current, include_links=include_links):
            return True
        current = current.parent

    return False


def is_skipped_element(element: Tag, include_links: bool = True) -> bool:
    skip_tags = AUDIO_BLOCK_SKIP_TAGS if include_links else AUDIO_TEXT_SKIP_TAGS
    if element.name in skip_tags:
        return True

    return has_any_class(element, AUDIO_SKIP_CLASSES)


def has_any_class(element: Tag, class_names: set[str]) -> bool:
    return any(class_name in class_names for class_name in element.get("class", []))


def collect_sentence_ids(root: Tag, builder: ReaderAudioMapBuilder) -> list[str]:
    output = []

    if root.name in AUDIO_HEADING_TAGS:
        return list(builder.heading_sentence_ids.get(id(root), []))

    if root.name in AUDIO_BLOCK_TAGS:
        output.extend(builder.block_sentence_ids.get(id(root), []))

    for element in get_audio_targets(root):
        if element.name in AUDIO_HEADING_TAGS:
            output.extend(builder.heading_sentence_ids.get(id(element), []))
        else:
            output.extend(builder.block_sentence_ids.get(id(element), []))

    return output


def get_section_sentence_ids(heading: Tag, builder: ReaderAudioMapBuilder) -> list[str]:
    output = []
    heading_level = get_heading_level(heading)
    element = heading.next_sibling

    while element:
        if not isinstance(element, Tag):
            element = element.next_sibling
            continue

        if element.name in AUDIO_HEADING_TAGS and get_heading_level(element) <= heading_level:
            break

        output.extend(collect_sentence_ids(element, builder))
        element = element.next_sibling

    return output


def get_heading_level(heading: Tag) -> int:
    match = re.fullmatch(r"h([1-6])", heading.name or "")
    return int(match.group(1)) if match else 1
