from pathlib import Path

from piggy.utils import get_mimetype

# Any image in this folder is an emote named after the file, e.g. party.webp is :party:
EMOTES_FOLDER = Path(__file__).parent / "static" / "img" / "emotes"
# Alt text for emotes whose name doesn't describe them; diff1-5 are also the difficulty icons on cards
EMOTE_ALT_TEXT = {f"diff{level}": f"Vanskelighetsgrad {level} av 5" for level in range(1, 6)}


def get_emotes() -> dict[str, dict]:
    """Map piggy's `:name:` emote shortcodes to the <img> attributes they render as (on top of twemoji)."""
    images = sorted(EMOTES_FOLDER.iterdir()) if EMOTES_FOLDER.is_dir() else []
    return {
        image.stem: {
            "src": f"/static/img/emotes/{image.name}",
            "alt": EMOTE_ALT_TEXT.get(image.stem, image.stem.replace("_", " ")),
            # Keeping the twemoji class makes the image lightbox (glightbox) leave emotes alone, like other emoji
            "class": "twemoji emote",
        }
        for image in images
        if (get_mimetype(image.name) or "").startswith("image/")
    }


EMOTES = get_emotes()
