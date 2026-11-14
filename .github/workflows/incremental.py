"""
Decides what the GitHub Pages build has to rebuild, using the state the previous build left in STATE_FILE.

The build is full when there is no previous build, when piggy itself or its installed packages changed, or when a
changed content file can't be traced to pages. Otherwise only the pages a changed file belongs to are rebuilt,
together with every page that shows something about them:

- every page in the topic of a changed page or attachment (the level selector, and the translations of each level),
- every page below a folder whose meta.json or media changed,
- the folders above those pages (their cards),
- every page that linked to them in the previous build (relevant pages, "Brukt i", shortlinks, links in the text).

After that round, the scraper also rebuilds the pages a rebuilt page started or stopped linking to ("Brukt i").
"""

import hashlib
import importlib.metadata
import json
import os
import subprocess
from pathlib import Path

STATE_FILE = Path(".demo-state.json")


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _git(repository: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repository), *args], capture_output=True, text=True, encoding="utf-8")


def piggy_fingerprint(root: Path) -> str:
    """What every page depends on: piggy's commit, its uncommitted changes and the installed packages."""
    packages = sorted(
        f"{dist.metadata['Name']}=={dist.version} {dist.read_text('direct_url.json') or ''}"
        for dist in importlib.metadata.distributions()
    )
    commit = _git(root, "rev-parse", "HEAD").stdout
    uncommitted = _git(root, "diff", "HEAD", "--", ".", ":(exclude)piggybank").stdout
    return hashlib.sha256("\n".join([commit, uncommitted, *packages]).encode()).hexdigest()


def content_revision(piggybank: Path) -> str:
    return _git(piggybank, "rev-parse", "HEAD").stdout.strip()


def changed_files(piggybank: Path, old: str, new: str) -> set[str] | None:
    """The content files that differ between two commits, or None when they can't be compared."""
    if not old:
        return None
    result = _git(piggybank, "diff", "--name-only", "--no-renames", "-z", old, new)
    if result.returncode:
        return None
    return {path for path in result.stdout.split("\0") if path}


def _folder(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""


def _topic(source: str) -> str | None:
    """The folder of a page's markdown file (for a translation, the folder of the page it translates)."""
    if not source.endswith(".md"):
        return None
    parts = source.split("/")
    return "/".join(parts[: parts.index("translations")]) if "translations" in parts else _folder(source)


def _owner(file: str) -> tuple[str, str] | None:
    """What a changed content file belongs to: ("topic", folder) or ("tree", folder); None if we can't tell."""
    parts = file.split("/")
    for marker in ("attachments", "translations"):
        if marker in parts:
            return "topic", "/".join(parts[: parts.index(marker)])
    if "media" in parts:
        return "tree", "/".join(parts[: parts.index("media")])
    if parts[-1] in ("meta.json", "meta.oink"):
        return "tree", _folder(file)
    if file.endswith((".md", ".oink")):
        return "topic", _folder(file)
    return None


def _ancestors(folder: str) -> list[str]:
    """The folder and every folder above it, up to the root ("")."""
    folders = [folder]
    while folder:
        folder = _folder(folder)
        folders.append(folder)
    return folders


def affected_pages(changed: set[str], sources: dict[str, str], links: dict[str, list[str]]) -> set[str] | None:
    """
    Return the pages to rebuild for changed content files, or None when only a full build is safe.

    :param changed: content files that changed, relative to the piggybank folder
    :param sources: page -> the markdown file or folder it is built from, relative to the piggybank folder
    :param links: page -> the pages it linked to in the previous build
    """
    pages = set()
    for file in changed:
        owner = _owner(file)
        if owner is None or owner == ("tree", ""):
            return None  # Unknown files, or the root folder's metadata which every page shows
        kind, folder = owner
        pages |= {
            page
            for page, source in sources.items()
            if source == folder
            or (kind == "topic" and _topic(source) == folder)
            or (kind == "tree" and source.startswith(f"{folder}/"))
        }

    folder_pages = {source: page for page, source in sources.items() if _topic(source) is None}
    linked_from = {}
    for page, targets in links.items():
        for target in targets:
            linked_from.setdefault(target, set()).add(page)

    for page in list(pages):
        source = sources[page]
        folder = _topic(source) if _topic(source) is not None else source
        pages |= {folder_pages[ancestor] for ancestor in _ancestors(folder) if ancestor in folder_pages}
        pages |= linked_from.get(page, set())
    return pages


def plan(
    state: dict, fingerprint: str, revision: str, piggybank: Path, sources: dict[str, str], output: Path
) -> tuple[set[str] | None, set[str], str]:
    """Return (pages to rebuild, changed content files, why); the pages are None when the build has to be full."""
    if os.environ.get("FORCE_FULL_REBUILD", "").lower() == "true":
        return None, set(), "FORCE_FULL_REBUILD is set"
    if not state or not output.is_dir():
        return None, set(), "there is no previous build"
    if state.get("piggy") != fingerprint:
        return None, set(), "piggy or its packages changed"
    changed = changed_files(piggybank, state.get("piggybank", ""), revision)
    if changed is None:
        return None, set(), "the previous content revision can't be compared"
    pages = affected_pages(changed, {**state.get("sources", {}), **sources}, state.get("links", {}))
    if pages is None:
        return None, set(), "a changed content file can't be traced to pages"
    return pages, changed, f"{len(changed)} content files changed"
