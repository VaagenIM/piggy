"""Repair converter navigation before the body enters Piggy's page layout."""

from collections.abc import Callable
import re
from urllib.parse import unquote, urlsplit, urlunsplit

from bs4 import BeautifulSoup


def repair_rendered_navigation(body: str, *, route: str, normalize_page_path: Callable[[str], str]) -> str:
    """Normalize local Markdown page paths while preserving queries and fragments.

    The layout owns the skip link: the converter's target can disappear when
    its H1 is replaced by Piggy's title. External links and media are untouched.
    """
    soup = BeautifulSoup(body, "html.parser")
    changed = False
    # roamlinks uses GFM anchors, while Markdown's default TOC removes accents
    # and some Norwegian letters. Keep the existing IDs and add GFM aliases.
    existing_ids = {tag["id"] for tag in soup.find_all(id=True)}
    for heading in soup.find_all(re.compile(r"^h[1-6]$"), id=True):
        text = (
            "".join(value for value in heading.strings if not value.find_parent("a", class_="headerlink"))
            .strip()
            .lower()
        )
        alias = re.sub(r" +", "-", re.sub(r"[^\w\u4e00-\u9fff\- ]", "", text))
        if alias and alias not in existing_ids:
            anchor = soup.new_tag("span", id=alias)
            anchor["aria-hidden"] = "true"
            heading.insert(0, anchor)
            existing_ids.add(alias)
            changed = True

    for link in soup.find_all("a"):
        if "md-skip" in link.get("class", []):
            link.decompose()
            changed = True
            continue

        href = link.get("href")
        if not href or not href.startswith(f"/{route}/"):
            continue
        parts = urlsplit(href)
        if parts.scheme or parts.netloc:
            continue
        path = unquote(parts.path)
        if not path.startswith(f"/{route}/") or not path.endswith(".md"):
            continue
        path = normalize_page_path(path[:-3])
        link["href"] = urlunsplit(parts._replace(path=path))
        changed = True

    return str(soup) if changed else body
