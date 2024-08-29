from io import BytesIO
from pathlib import Path

from flask import send_file

from piggy.models import LANGUAGES


def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, "webp", quality=100)
    img_io.seek(0)
    return send_file(img_io, mimetype="image/webp")


def get_supported_languages(assignment_path: Path):
    languages = {
        iso_code: lang
        for iso_code, lang in LANGUAGES.items()
        if (assignment_path.parent / "translations" / iso_code / assignment_path.name).exists()
    }
    return {"": LANGUAGES[""], **languages}
