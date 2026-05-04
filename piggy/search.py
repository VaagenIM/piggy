import re
from collections import Counter

# Norwegian + English stopwords — removed before counting so they don't
# inflate frequencies or waste slots in the top-60 list
# fmt: off
_STOPWORDS = {
    # Norwegian
    "og", "i", "er", "på", "til", "av", "som", "en", "et", "for", "med",
    "den", "det", "de", "ikke", "om", "fra", "kan", "har", "vi", "at",
    "var", "men", "seg", "så", "han", "hun", "nå", "der", "dem", "ble",
    "bli", "inn", "alle", "når", "du", "skal", "litt", "ha", "her",
    "også", "noe", "dette", "hvordan", "hjelp", "ved", "lag", "lage",
    "bruk", "prøv",
    # English
    "the", "a", "an", "and", "or", "is", "in", "it", "of", "to", "that",
    "this", "with", "on", "are", "as", "be", "by", "from", "has", "have",
    "not", "was", "were", "will", "you", "we", "he", "she", "they", "do",
    "if", "can", "its", "but", "then", "than", "so", "up", "out", "into",
    "no", "use", "used", "using",
    # URL / web noise
    "https", "http", "www", "com", "org", "net", "asp", "html",
    "attachments", "webp", "png", "jpg", "jpeg", "svg", "gif",
    # Layout / markdown noise
    "center", "left", "right", "ex",
}
# fmt: on


def parse_body(file_path: str) -> tuple[str, str]:
    """
    Read the markdown body and return:
      - snippet: display-safe text
      - tokens:  TF-weighted token string for lunr indexing.

    How the token string works:
      lunr tokenizes, trims, stopword-filters, and Porter-stems each field string at
      index time — so we must NOT pre-stem (our stems wouldn't match Porter's query
      output). Also, term^N boost syntax is query-only in lunr and silently breaks
      when used in document fields (it becomes the tokens ["term", "N"]).

      Instead: remove stopwords early to keep term counts meaningful, count raw token
      frequencies, then repeat each of the top 60 tokens 1–4 times proportional to
      its normalised TF. lunr then sees realistic term frequency for BM25 scoring
      while we send a fraction of the original text.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError:
        return "", ""

    # Strip frontmatter
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        raw = raw[end + 4 :] if end != -1 else raw

    # -- snippet: strip code blocks entirely for safe display --
    snippet = re.sub(r"\s*```.*?```", " ", raw, flags=re.DOTALL)
    snippet = re.sub(r"`{1}", "", snippet)
    snippet = re.sub(r"^\s*>.*$", "", snippet, flags=re.MULTILINE)  # blockquotes/callouts
    snippet = re.sub(r"^\s*={3}.*$", "", snippet, flags=re.MULTILINE)  # content blocks headings
    snippet = re.sub(r"^\s*\|.*\|.*$", "", snippet, flags=re.MULTILINE)  # table rows
    snippet = re.sub(r"^\s*[-|: ]+$", "", snippet, flags=re.MULTILINE)  # table separators / horizontal rules
    snippet = re.sub(r"^\s*#+\s+.*$", "", snippet, flags=re.MULTILINE)  # headings
    snippet = re.sub(r"^\s*[-*+]\s+.*$", "", snippet, flags=re.MULTILINE)  # unordered lists
    snippet = re.sub(r"^\s*\d+\.\s+.*$", "", snippet, flags=re.MULTILINE)  # ordered lists
    snippet = re.sub(r"!\[.*?]\(.*?\)", " ", snippet)  # images
    snippet = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", snippet)  # links: keep label
    snippet = re.sub(r"\[\[([^|\]]+)\|([^\]]+)]]", r"\2", snippet)  # wikilinks with display text
    snippet = re.sub(r"\[\[([^\]]+)]]", r"\1", snippet)  # wikilinks without display text
    snippet = re.sub(r"<[^>]+>", " ", snippet)  # html tags
    snippet = re.sub(r"[*_~]+", "", snippet)  # inline bold/italic/strikethrough
    snippet = re.sub(r"\\+", "", snippet)  # backslashes
    snippet = re.sub(r"\s+", " ", snippet).strip()

    # -- tokens: keep code block contents (strip fences), clean markup --
    body = re.sub(r"```[a-zA-Z]*\n?", "", raw)
    body = re.sub(r"`([^`]+)`", r"\1", body)
    body = re.sub(r"!\[.*?]\(.*?\)", " ", body)  # remove images (path noise)
    body = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", body)  # links: keep label only
    body = re.sub(r"\[\[([^|\]]+)\|([^\]]+)]]", r"\2", body)  # wikilinks with display text
    body = re.sub(r"\[\[([^\]]+)]]", r"\1", body)  # wikilinks without display text
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"[*_~|#>!`\[\]()\-]+", " ", body)
    body = body.lower()

    # Tokenize: alphanumeric tokens ≥ 2 chars, stopwords removed
    all_tokens = [t for t in re.findall(r"[a-z0-9æøå]{2,}", body) if t not in _STOPWORDS]

    if not all_tokens:
        return snippet[:400], ""

    # Count raw token frequencies (Counter keys are already unique)
    tf = Counter(all_tokens)
    max_freq = tf.most_common(1)[0][1]

    # Repeat each of the top 60 tokens 1–4 times proportional to normalised TF
    token_parts = []
    for term, freq in tf.most_common(60):
        repeats = max(1, round(4 * freq / max_freq))
        token_parts.extend([term] * repeats)

    return snippet[:400], " ".join(token_parts)


def build_search_index(piggymap: dict) -> list[dict]:
    """Walk the piggymap and return a flat list of search index documents."""
    results = []

    def _walk(node: dict, path_parts: list, label_parts: list):
        for key, value in node.items():
            if key == "meta":
                continue
            if not isinstance(value, dict):
                continue
            if "path" in value:
                # Leaf: assignment file
                meta = value.get("meta", {})
                url_path = "/".join(path_parts + [key])
                file_path = value.get("path", "")
                snippet, body = parse_body(str(file_path)) if file_path else ("", "")
                title = value.get("level_name") or value.get("heading") or key
                # Build breadcrumb as a flat label array — JS reconstructs URLs from the id
                results.append(
                    {
                        "id": url_path,
                        "title": title,
                        "breadcrumb": label_parts,
                        "content": snippet,
                        "body": body,
                    }
                )
            else:
                # Directory node: prefer meta.json "name" over raw key
                node_meta = value.get("meta", {})
                label = node_meta.get("name") or key.replace("_", " ")
                data = value.get("data", {k: v for k, v in value.items() if k != "meta"})
                _walk(data, path_parts + [key], label_parts + [label])

    _walk(dict(piggymap), [], [])
    return results
