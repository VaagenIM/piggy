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
AUDIO_SKIP_CLASSES = {"highlight", "MathJax", "md-code__nav", "settings-reader-preview"}
SENTENCE_BOUNDARY_CHARS = ".!?"
SENTENCE_CLOSING_CHARS = "\"')]}»”’"
ABBREVIATIONS = {
    "adm",
    "bl.a",
    "ca",
    "dvs",
    "e.g",
    "etc",
    "f.eks",
    "fig",
    "i.e",
    "kap",
    "m.m",
    "mr",
    "mrs",
    "ms",
    "nr",
    "osv",
    "prof",
    "st",
    "vs",
}
CODE_FILE_EXTENSIONS = {
    "bat",
    "c",
    "cpp",
    "cs",
    "css",
    "csv",
    "db",
    "env",
    "gif",
    "go",
    "html",
    "java",
    "jpeg",
    "jpg",
    "js",
    "json",
    "jsx",
    "log",
    "m4a",
    "md",
    "mp3",
    "ogg",
    "opus",
    "pdf",
    "php",
    "png",
    "py",
    "rb",
    "rs",
    "sh",
    "sql",
    "svg",
    "toml",
    "ts",
    "tsx",
    "txt",
    "wav",
    "webm",
    "webp",
    "yaml",
    "yml",
    "zip",
}
DOCTYPE_RE = re.compile(r"<!\s*doctype\s+html\s*>", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<\s*(/)?\s*([a-zA-Z][\w:-]*)(?:\s+[^<>]*)?>")
LATEX_INLINE_RE = re.compile(r"\\\((.*?)\\\)|\\\[(.*?)\\\]")
LATEX_COMMAND_REPLACEMENTS = (
    ("\\cdot", " times "),
    ("\\times", " times "),
    ("\\lfloor", "floor of "),
    ("\\rfloor", ""),
    ("\\left", ""),
    ("\\right", ""),
)
LATEX_BACKSLASH_COMMAND_RE = re.compile(r"\\([A-Za-z]+)")
FUNCTION_CALL_RE = re.compile(r"\b([A-Za-z_][\w-]*)\s*\(\)")
FUNCTION_ARGS_RE = re.compile(r"\b([A-Za-z_][\w-]*)\(\s*([^()]{1,32})\s*\)")
SHELL_POSITIONAL_ARG_RE = re.compile(r"\$(\d+)")
PYTHON_REVERSE_SLICE_RE = re.compile(r"\b([A-Za-z_][\w-]*)\s*\[\s*::\s*-1\s*\]")
INDEX_ACCESS_RE = re.compile(r"\b([A-Za-z_][\w-]*)\[\s*([A-Za-z_][\w-]*|\d+)\s*\]")
EMPTY_BRACKETS_RE = re.compile(r"\[\s*\]")
BRACKETED_LIST_RE = re.compile(r"\[([^\[\]]*,[^\[\]]*)\]")
CITATION_LABEL_RE = re.compile(r"\s*\[[A-Za-z]\]\s*")
SIMPLE_BRACKETS_RE = re.compile(r"\[([^\[\]]{1,48})\]")
QUOTED_CODE_TOKEN_RE = re.compile(r"[\"“”']([A-Za-z0-9_]+)[\"“”']")
SPACE_BEFORE_PUNCTUATION_RE = re.compile(r"\s+([,.;:!?])")
DUPLICATE_COMMA_RE = re.compile(r",\s*,+")
FILE_EXTENSION_RE = re.compile(
    r"\b([A-Za-z0-9][A-Za-z0-9_-]*)\.([A-Za-z0-9]{1,8})\b"
)
STANDALONE_EXTENSION_RE = re.compile(r"(?<![\w.])\.([A-Za-z0-9]{1,8})\b")
SPACED_ASCII_ARROW_RE = re.compile(r"\s+-\s+>\s*")
INLINE_ARROW_RE = re.compile(r"(?<=\S)\s*(?:->|→|⇒|⟶)\s*(?=\S)")
LEADING_ARROW_RE = re.compile(r"(^|\s)(?:->|→|⇒|⟶)\s*")
COMPARISON_REPLACEMENTS = (
    (re.compile(r"!="), " is not equal to "),
    (re.compile(r"=="), " equals "),
    (re.compile(r">="), " greater than or equal to "),
    (re.compile(r"<="), " less than or equal to "),
    (re.compile(r"(?<=\S)\s+>\s+(?=\S)"), " greater than "),
    (re.compile(r"(?<=\S)\s+<\s+(?=\S)"), " less than "),
)
SPACED_MULTIPLY_RE = re.compile(r"\s+\*\s+")
SPACED_PLUS_RE = re.compile(r"\s+\+\s+")
SPACED_EQUALS_RE = re.compile(r"\s+=\s+")
SPACED_NUMERIC_MINUS_RE = re.compile(r"(?<=\d)\s+-\s+(?=\d)")
NUMERIC_FACTORIAL_RE = re.compile(r"(?<=\d)!(?=\s*(?:$|=|,|\)|\]|}|\*|·|times))")
EMOJI_RE = re.compile(
    "["
    "\U00002600-\U000027bf"
    "\U0001f000-\U0001faff"
    "\ufe0f"
    "]+"
)


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

    sentences = []
    start = 0
    i = 0

    while i < len(text):
        boundary_end = get_sentence_boundary_end(text, i)
        if boundary_end == -1:
            i += 1
            continue

        append_normalized_sentence(sentences, text[start:boundary_end])
        start = skip_whitespace(text, boundary_end)
        i = start

    append_normalized_sentence(sentences, text[start:])
    return sentences


def append_normalized_sentence(sentences: list[str], text: str) -> None:
    normalized = normalize_reader_text(text)
    if normalized:
        sentences.append(normalized)


def get_sentence_boundary_end(text: str, index: int) -> int:
    char = text[index]
    if char not in SENTENCE_BOUNDARY_CHARS:
        return -1

    if is_inside_angle_token(text, index):
        return -1
    if is_inside_function_token(text, index):
        return -1
    if char == "!" and is_factorial_marker(text, index):
        return -1

    if char == "." and not is_period_sentence_boundary(text, index):
        return -1

    if char in "!?" and index > 0 and text[index - 1] == "<":
        return -1

    end = index + 1
    while end < len(text) and text[end] in SENTENCE_BOUNDARY_CHARS:
        end += 1

    while end < len(text) and text[end] in SENTENCE_CLOSING_CHARS:
        end += 1

    if end >= len(text):
        return end

    if not text[end].isspace():
        return -1

    return end


def is_period_sentence_boundary(text: str, index: int) -> bool:
    previous_char = text[index - 1] if index > 0 else ""
    next_char = text[index + 1] if index + 1 < len(text) else ""

    if previous_char == "." or next_char == ".":
        return next_char != "."

    if previous_char.isdigit() and next_char.isdigit():
        return False

    if previous_char.isalnum() and next_char.isalnum():
        return False

    if is_spaced_initial_period(text, index):
        return False

    if is_known_abbreviation(text, index):
        return False

    return True


def is_spaced_initial_period(text: str, index: int) -> bool:
    token_start = index
    while token_start > 0 and text[token_start - 1].isalpha():
        token_start -= 1

    token = text[token_start:index]
    if len(token) != 1 or not token.isalpha():
        return False

    next_index = skip_whitespace(text, index + 1)
    if (
        next_index + 1 < len(text)
        and text[next_index].isalpha()
        and text[next_index + 1] == "."
    ):
        return True

    previous_index = token_start - 1
    while previous_index >= 0 and text[previous_index].isspace():
        previous_index -= 1

    if previous_index < 0 or text[previous_index] != ".":
        return False

    previous_token_end = previous_index
    previous_token_start = previous_token_end
    while previous_token_start > 0 and text[previous_token_start - 1].isalpha():
        previous_token_start -= 1

    previous_token = text[previous_token_start:previous_token_end]
    return len(previous_token) == 1 and previous_token.isalpha()


def is_known_abbreviation(text: str, index: int) -> bool:
    token_start = index
    while token_start > 0 and re.match(r"[\w.]", text[token_start - 1], re.UNICODE):
        token_start -= 1

    token = text[token_start:index].strip(".").lower()
    if token in ABBREVIATIONS:
        return True

    parts = [part for part in token.split(".") if part]
    return len(parts) > 1 and all(len(part) == 1 and part.isalpha() for part in parts)


def is_inside_angle_token(text: str, index: int) -> bool:
    token_start = text.rfind("<", 0, index + 1)
    if token_start == -1:
        return False

    previous_close = text.rfind(">", 0, index + 1)
    if previous_close > token_start:
        return False

    token_end = text.find(">", index + 1)
    if token_end == -1:
        return False

    token = text[token_start : token_end + 1]
    return bool(DOCTYPE_RE.fullmatch(token) or HTML_TAG_RE.fullmatch(token))


def is_inside_function_token(text: str, index: int) -> bool:
    token_start = text.rfind("(", 0, index + 1)
    if token_start <= 0:
        return False

    previous_close = text.rfind(")", 0, index + 1)
    if previous_close > token_start:
        return False

    token_end = text.find(")", index + 1)
    if token_end == -1:
        return False

    if not re.match(r"[\w-]", text[token_start - 1], re.UNICODE):
        return False

    return bool(re.match(r"[A-Za-z_][\w-]*$", text[:token_start].rsplit(maxsplit=1)[-1]))


def is_factorial_marker(text: str, index: int) -> bool:
    if index <= 0 or not re.match(r"[\w)]", text[index - 1], re.UNICODE):
        return False

    next_index = skip_whitespace(text, index + 1)
    if next_index >= len(text):
        return False

    return text[next_index] in {"=", ",", ")", "]", "}", "·", "*"}


def skip_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1

    return index


def prepare_sentence_audio_text(text: str) -> str:
    """Make generated/recorded sentence text friendlier for speech."""
    text = normalize_reader_text(text)
    text = normalize_latex_audio_text(text)
    text = EMOJI_RE.sub("", text)
    text = DOCTYPE_RE.sub("DOCTYPE html", text)
    text = HTML_TAG_RE.sub(format_html_tag_for_audio, text)
    text = SHELL_POSITIONAL_ARG_RE.sub(r"argument \1", text)
    text = PYTHON_REVERSE_SLICE_RE.sub(r"\1 reverse slice", text)
    text = INDEX_ACCESS_RE.sub(r"\1 index \2", text)
    text = EMPTY_BRACKETS_RE.sub("empty list", text)
    text = BRACKETED_LIST_RE.sub(r"\1", text)
    text = CITATION_LABEL_RE.sub(" ", text)
    text = SIMPLE_BRACKETS_RE.sub(r"\1", text)
    text = QUOTED_CODE_TOKEN_RE.sub(r"\1", text)
    text = FUNCTION_CALL_RE.sub(r"\1 function", text)
    text = FUNCTION_ARGS_RE.sub(format_function_args_for_audio, text)
    text = FILE_EXTENSION_RE.sub(format_file_extension_for_audio, text)
    text = STANDALONE_EXTENSION_RE.sub(format_standalone_extension_for_audio, text)
    text = SPACED_ASCII_ARROW_RE.sub(", ", text)
    text = INLINE_ARROW_RE.sub(" to ", text)
    text = LEADING_ARROW_RE.sub(r"\1", text)
    for pattern, replacement in COMPARISON_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    text = NUMERIC_FACTORIAL_RE.sub(" factorial", text)
    text = SPACED_MULTIPLY_RE.sub(" times ", text)
    text = SPACED_PLUS_RE.sub(" plus ", text)
    text = SPACED_EQUALS_RE.sub(" equals ", text)
    text = SPACED_NUMERIC_MINUS_RE.sub(" minus ", text)
    text = DUPLICATE_COMMA_RE.sub(",", text)
    text = SPACE_BEFORE_PUNCTUATION_RE.sub(r"\1", text)
    return normalize_reader_text(text)


def normalize_latex_audio_text(text: str) -> str:
    text = LATEX_INLINE_RE.sub(lambda match: match.group(1) or match.group(2) or "", text)
    for source, replacement in LATEX_COMMAND_REPLACEMENTS:
        text = text.replace(source, replacement)
    text = LATEX_BACKSLASH_COMMAND_RE.sub(r"\1", text)
    return text


def format_html_tag_for_audio(match: re.Match) -> str:
    tag_name = match.group(2).replace("-", " ")
    if match.group(1):
        return f"closing {tag_name}"

    return tag_name


def format_file_extension_for_audio(match: re.Match) -> str:
    stem, extension = match.groups()
    if extension.lower() not in CODE_FILE_EXTENSIONS:
        return match.group(0)

    return f"{stem} dot {extension}"


def format_function_args_for_audio(match: re.Match) -> str:
    function_name, args = match.groups()
    args = normalize_reader_text(args.replace("!", " factorial").replace("^", " to the power of "))
    return f"{function_name} of {args}"


def format_standalone_extension_for_audio(match: re.Match) -> str:
    extension = match.group(1)
    if extension.lower() not in CODE_FILE_EXTENSIONS:
        return match.group(0)

    return f"dot {extension}"


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

    def add_sentence(self, text: str) -> str | None:
        text = prepare_sentence_audio_text(text)
        if not text:
            return None

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

    def add_sentences(self, texts: list[str]) -> list[str]:
        return [
            sentence_id
            for text in texts
            if (sentence_id := self.add_sentence(text))
        ]

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
        self.page_heading_sentence_ids = self.add_sentences(split_reader_sentences(text))

    def add_heading(self, heading: Tag) -> None:
        heading_text = get_element_audio_text(heading)
        self.heading_sentence_ids[id(heading)] = self.add_sentences(split_reader_sentences(heading_text))

    def add_block(self, block: Tag) -> None:
        block_text = get_element_audio_text(block, include_nested_containers=False)
        if not block_text:
            return

        sentence_texts = split_reader_sentences(block_text) or [block_text]
        sentence_ids = self.add_sentences(sentence_texts)
        if not sentence_ids:
            return

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
    if not normalize_reader_text(get_element_audio_text(element, include_nested_containers=False)):
        return False
    if has_skipped_ancestor(element):
        return False

    for child in element.find_all(recursive=False):
        if has_any_class(child, {"highlight"}):
            return False

    return True


def get_element_audio_text(element: Tag, include_nested_containers: bool = True) -> str:
    chunks = []

    for descendant in element.descendants:
        if not isinstance(descendant, NavigableString):
            continue
        if has_skipped_ancestor(descendant, stop_at=element, include_links=False):
            continue
        if not include_nested_containers and has_nested_container_ancestor(descendant, stop_at=element):
            continue
        chunks.append(str(descendant))

    return normalize_reader_text("".join(chunks))


def has_nested_container_ancestor(node: NavigableString, stop_at: Tag) -> bool:
    current = node.parent

    while isinstance(current, Tag) and current is not stop_at:
        if current.name in AUDIO_CONTAINER_CHILD_TAGS or has_any_class(current, {"highlight"}):
            return True
        current = current.parent

    return False


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
