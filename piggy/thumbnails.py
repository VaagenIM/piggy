import math
import random
import textwrap
from hashlib import md5
from pathlib import Path

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

from piggy.utils import lru_cache_wrapper

_FONTS_DIR = Path(__file__).parent / "static" / "fonts"

# Available TTF fonts for thumbnail text (Pillow can't use woff/woff2)
_FONT_PATHS = [
    _FONTS_DIR / "Lato-Bold.ttf",
    _FONTS_DIR / "Lato-Regular.ttf",
    _FONTS_DIR / "Lato-Light.ttf",
    _FONTS_DIR / "LEXIB___.ttf",
    _FONTS_DIR / "LEXIA___.ttf",
]


def _seed_from_text(title: str, seed: str = "") -> int:
    """Derive a deterministic seed from title + optional seed string."""
    return int(md5((title + seed).encode()).hexdigest(), 16)


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _blend_color(hex1: str, hex2: str, factor: float) -> str:
    """Blend hex1 towards hex2 by *factor*. Returns '#rrggbb'."""
    r1, g1, b1 = _hex_to_rgb(hex1)
    r2, g2, b2 = _hex_to_rgb(hex2)
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# Pattern drawing functions
# Each pattern should produce a visually *distinct* look.
# They receive two accent colours (accent1 stronger, accent2 softer) so they
# can create depth.
# ---------------------------------------------------------------------------


def _draw_diagonal_stripes(draw, w, h, rng, a1, a2):
    """Gentle diagonal stripes as a background texture."""
    stripe_w = rng.randint(18, 35)
    gap = stripe_w + rng.randint(40, 80)
    direction = rng.choice([-1, 1])
    for i in range(-h, w + h, gap):
        x0 = i
        if direction == 1:
            draw.polygon(
                [(x0, 0), (x0 + stripe_w, 0), (x0 + stripe_w - h, h), (x0 - h, h)],
                fill=a2,
            )
        else:
            draw.polygon(
                [(x0, 0), (x0 + stripe_w, 0), (x0 + stripe_w + h, h), (x0 + h, h)],
                fill=a2,
            )


def _draw_halftone_dots(draw, w, h, rng, a1, a2):
    """Grid-aligned dots that grow/shrink based on position — subtle halftone feel."""
    cols = rng.randint(10, 16)
    rows = rng.randint(5, 8)
    cell_w = w / cols
    cell_h = h / rows
    max_r = min(cell_w, cell_h) * 0.25
    mode = rng.choice(["radial", "horizontal", "vertical"])
    for col in range(cols):
        for row in range(rows):
            cx = cell_w * (col + 0.5)
            cy = cell_h * (row + 0.5)
            if mode == "radial":
                dist = math.hypot(cx - w / 2, cy - h / 2) / math.hypot(w / 2, h / 2)
            elif mode == "horizontal":
                dist = cx / w
            else:
                dist = cy / h
            r = max_r * (0.2 + 0.8 * dist)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=a2)


def _draw_corner_blobs(draw, w, h, rng, a1, a2):
    """Soft circles anchored to edges — gentle organic accent."""
    corners = [(0, 0), (w, 0), (0, h), (w, h)]
    rng.shuffle(corners)
    count = rng.randint(1, 2)
    for cx, cy in corners[:count]:
        r = rng.randint(70, 140)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=a2)


def _draw_diamond_scatter(draw, w, h, rng, a1, a2):
    """Scattered diamond shapes at varying sizes — a geometric confetti feel."""
    count = rng.randint(6, 14)
    for _ in range(count):
        cx = rng.randint(0, w)
        cy = rng.randint(0, h)
        size = rng.randint(10, 30)
        draw.polygon(
            [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)],
            fill=a2 if rng.random() > 0.3 else a1,
        )


def _draw_concentric_rings(draw, w, h, rng, a1, a2):
    """Faint concentric circles radiating from an off-center point."""
    cx = rng.randint(w // 4, 3 * w // 4)
    cy = rng.randint(h // 4, 3 * h // 4)
    max_r = int(math.hypot(w, h) * 0.55)
    ring_gap = rng.randint(30, 55)
    thickness = rng.randint(2, 4)
    r = ring_gap
    while r < max_r:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=a2, width=thickness)
        r += ring_gap


def _draw_chevrons(draw, w, h, rng, a1, a2):
    """Gentle repeating chevron lines."""
    spacing = rng.randint(40, 65)
    thickness = rng.randint(2, 5)
    vertical = rng.random() > 0.5
    if vertical:
        for y in range(0, h + spacing, spacing):
            pts = [(0, y), (w // 2, y - spacing // 3), (w, y)]
            draw.line(pts, fill=a2, width=thickness)
    else:
        for x in range(0, w + spacing, spacing):
            pts = [(x, 0), (x - spacing // 3, h // 2), (x, h)]
            draw.line(pts, fill=a2, width=thickness)


def _draw_wave_bands(draw, w, h, rng, a1, a2):
    """Gentle sine-wave lines across the image."""
    count = rng.randint(2, 3)
    for i in range(count):
        amplitude = rng.randint(15, 35)
        freq = rng.uniform(0.006, 0.015)
        phase = rng.uniform(0, 2 * math.pi)
        y_base = int(h * (i + 1) / (count + 1))
        thickness = rng.randint(2, 5)
        points = [(x, y_base + amplitude * math.sin(freq * x + phase)) for x in range(0, w, 3)]
        if len(points) >= 2:
            draw.line(points, fill=a2, width=thickness)


def _draw_cross_hatch(draw, w, h, rng, a1, a2):
    """Faint cross-hatch lines for a light texture."""
    spacing = rng.randint(35, 55)
    thickness = rng.randint(1, 2)
    for i in range(-max(w, h), max(w, h) * 2, spacing):
        draw.line([(i, 0), (i - h, h)], fill=a2, width=thickness)
    for i in range(-max(w, h), max(w, h) * 2, spacing):
        draw.line([(i, 0), (i + h, h)], fill=a2, width=thickness)


_PATTERN_FUNCS = [
    _draw_diagonal_stripes,
    _draw_halftone_dots,
    _draw_corner_blobs,
    _draw_diamond_scatter,
    _draw_concentric_rings,
    _draw_chevrons,
    _draw_wave_bands,
    _draw_cross_hatch,
]


@lru_cache_wrapper
def create_thumbnail(
    title: str, bg_color: str = "111111", text_color: str = "fefefe", size: tuple[int, int] = (700, 300)
) -> PIL.Image:
    """Returns the image data for a thumbnail with decorative patterns and centered text."""
    w, h = size
    rng = random.Random(_seed_from_text(title, bg_color + text_color))

    im = PIL.Image.new("RGB", (w, h), "#" + bg_color)
    draw = PIL.ImageDraw.Draw(im)

    # --- Accent colours (bg blended toward text — kept subtle) ---
    accent1 = _blend_color(bg_color, text_color, rng.uniform(0.10, 0.18))
    accent2 = _blend_color(bg_color, text_color, rng.uniform(0.05, 0.12))

    # --- Decorative pattern layer (exactly 1 pattern — keeps each card distinct) ---
    pattern_fn = rng.choice(_PATTERN_FUNCS)
    pattern_fn(draw, w, h, rng, accent1, accent2)

    # --- Pick a font ---
    font_path = rng.choice(_FONT_PATHS)
    if not font_path.exists():
        font_path = _FONT_PATHS[0]  # fallback

    # --- Text rendering ---
    x_padding = 60
    y_padding = 80

    text = textwrap.fill(title, width=28)
    font_size = 180

    font = PIL.ImageFont.truetype(font_path.as_posix(), font_size)

    max_text_w = w - 2 * x_padding
    max_text_h = h - 2 * y_padding

    text_bbox = None
    recursions = 0
    while (
        (text_bbox is None or (text_bbox[2] - text_bbox[0]) > max_text_w or (text_bbox[3] - text_bbox[1]) > max_text_h)
        and font_size > 0
        and recursions < 50
    ):
        font = font.font_variant(size=font_size)
        text_bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
        font_size -= 5
        recursions += 1

    center = (w / 2, h / 2)
    draw.multiline_text(center, text, font=font, fill="#" + text_color, align="center", anchor="mm")

    return im
