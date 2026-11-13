from pathlib import Path

from piggy.utils import get_mimetype

# Any image in this folder is an emote named after the file, e.g. party.png is :party:
EMOTES_FOLDER = Path(__file__).parent / "static" / "img" / "emotes"


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
