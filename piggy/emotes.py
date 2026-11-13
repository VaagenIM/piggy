import re
from pathlib import Path

from piggy.utils import get_mimetype

# Any image in this folder is an emote named after the file, e.g. party.png is :party:
EMOTES_FOLDER = Path(__file__).parent / "static" / "img" / "emotes"


# Pages used to copy the difficulty icons into their attachments as diff1.png ... diff5.png
LEGACY_DIFFICULTY_ATTACHMENT_RE = re.compile(r"diff([1-5])\.\w+")


def get_legacy_difficulty_icon(filename: str) -> str | None:
    """Return the static difficulty icon for a missing `diffN` attachment (e.g. in a not yet retranslated page)."""
    if match := LEGACY_DIFFICULTY_ATTACHMENT_RE.fullmatch(Path(filename).name):
        return f"static/img/difficulties/{match.group(1)}.png"
    return None


def get_emotes() -> dict[str, dict]:
    """Map piggy's `:name:` emote shortcodes to the <img> attributes they render as (on top of twemoji)."""
    emotes = {
        f"diff{level}": {"src": f"/static/img/difficulties/{level}.png", "alt": f"Vanskelighetsgrad {level} av 5"}
        for level in range(1, 6)
    }
    for image in sorted(EMOTES_FOLDER.iterdir()) if EMOTES_FOLDER.is_dir() else []:
        if (get_mimetype(image.name) or "").startswith("image/"):
            emotes[image.stem] = {"src": f"/static/img/emotes/{image.name}", "alt": image.stem.replace("_", " ")}
    # Keeping the twemoji class makes the image lightbox (glightbox) leave emotes alone, like other emoji
    return {name: {**attributes, "class": "twemoji emote"} for name, attributes in emotes.items()}


EMOTES = get_emotes()
