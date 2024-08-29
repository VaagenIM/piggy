from flask import send_file
from io import BytesIO


def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, "webp", quality=100)
    img_io.seek(0)
    return send_file(img_io, mimetype="image/webp")
