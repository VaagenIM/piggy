import re

from piggy.piggybank import SHORTLINK_MAP

# A shortlink as copied from the site (https://piggy.iktim.no/s/<code>), or written as /s/<code> or s/<code>
SHORTLINK_URL_RE = re.compile(r"^(?:https?://[^/\s]+)?/?s/([0-9A-Za-z]+)/?$")

# The origin of a shortlink copied from one of the Piggy sites (piggy.iktim.no, piglet.iktim.no, ...) in an href
PIGGY_SITE_SHORTLINK_ORIGIN_RE = re.compile(
    r"""(?<=href=["'])https?://pig[^/\s"']*\.iktim\.no(?=/s/[0-9A-Za-z]+/?["'?#])"""
)


def resolve_shortlink(url: str) -> dict | None:
    """Return the page a shortlink url points to (target, title, ...), if it is a known shortlink."""
    match = SHORTLINK_URL_RE.match(url.strip())
    return SHORTLINK_MAP.get(match.group(1)) if match else None


def relativize_shortlinks(html: str) -> str:
    """Turn links to https://<piggy site>/s/<code> into /s/<code>, so they stay on the site the page is viewed on."""
    return PIGGY_SITE_SHORTLINK_ORIGIN_RE.sub("", html)


def split_md_link(link: str) -> tuple[str, str] | None:
    """
    Split a markdown link into (text, url), or None if it isn't one.

    Shortlinks point straight to their page, and a bare shortlink is a link titled after that page.
    """
    if not isinstance(link, str):
        return None

    text, separator, url = link.partition("](")
    text, url = (text[1:], url[:-1]) if separator else ("", link)

    if page := resolve_shortlink(url):
        return text or page["title"], page["target"]
    return (text, url) if separator else None
