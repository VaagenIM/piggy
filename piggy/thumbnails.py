import colorsys
import math
import random
from dataclasses import dataclass
from hashlib import md5
from pathlib import Path

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter
import PIL.ImageFont
import PIL.ImageOps

from piggy.utils import lru_cache_wrapper

_FONTS_DIR = Path(__file__).parent / "static" / "fonts" / "generator"

_FONT_PATHS = [
    # Reliable / general
    _FONTS_DIR / "Lato-Bold.ttf",
    _FONTS_DIR / "ArchivoBlack-Regular.ttf",
    _FONTS_DIR / "SpaceGrotesk-Bold.ttf",
    _FONTS_DIR / "Sora-ExtraBold.ttf",
    _FONTS_DIR / "LeagueSpartan-Bold.ttf",
    _FONTS_DIR / "Manrope-ExtraBold.ttf",
    _FONTS_DIR / "Montserrat-ExtraBold.ttf",
    _FONTS_DIR / "PlusJakartaSans-ExtraBold.ttf",
    _FONTS_DIR / "Outfit-ExtraBold.ttf",
    _FONTS_DIR / "Inter-Black.ttf",

    # Condensed / long-title friendly
    _FONTS_DIR / "BarlowCondensed-SemiBold.ttf",
    _FONTS_DIR / "Oswald-Bold.ttf",
    _FONTS_DIR / "FjallaOne-Regular.ttf",
    _FONTS_DIR / "RobotoCondensed-Bold.ttf",
    _FONTS_DIR / "IBMPlexSansCondensed-Bold.ttf",
    _FONTS_DIR / "ArchivoNarrow-Bold.ttf",
    _FONTS_DIR / "BebasNeue-Regular.ttf",

    # Technical / geometric
    _FONTS_DIR / "Rajdhani-Bold.ttf",
    _FONTS_DIR / "Oxanium-Bold.ttf",
    _FONTS_DIR / "ChakraPetch-Bold.ttf",
    _FONTS_DIR / "Exo2-Bold.ttf",
    _FONTS_DIR / "TitilliumWeb-Bold.ttf",
    _FONTS_DIR / "RussoOne-Regular.ttf",

    # More character / occasional
    _FONTS_DIR / "Anton-Regular.ttf",
    _FONTS_DIR / "Teko-SemiBold.ttf",
    _FONTS_DIR / "Bangers-Regular.ttfe",
    _FONTS_DIR / "ConcertOne-Regular.ttfe",
]


def _seed_from_text(title: str, seed: str = "") -> int:
    """Return a stable seed for a title/style combination."""
    return int(
        md5(f"{seed}\0{title}".encode("utf-8")).hexdigest(),
        16,
    )


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(
        int(value[i:i + 2], 16)
        for i in (0, 2, 4)
    )


def _rgb_to_hex(value: tuple[int, int, int]) -> str:
    return "".join(f"{max(0, min(255, channel)):02x}" for channel in value)


def _weighted_choice(
    scores: dict,
    rng: random.Random,
) -> str:
    """
    Deterministic weighted pick among named scores.

    Shared by the background-style/gradient-angle selection and the
    text-effect scoring system. Unsuitable candidates (score 0) never
    get picked, but among the remaining ones, better-scored options
    are more likely rather than guaranteed -- preserving variety
    between thumbnails whose contexts are merely "similar", not
    identical.
    """
    total = sum(max(0.0, score) for score in scores.values())

    if total <= 0:
        return next(iter(scores))

    pick = rng.uniform(0, total)
    cumulative = 0.0

    for key, score in scores.items():
        cumulative += max(0.0, score)

        if pick <= cumulative:
            return key

    return next(iter(scores))


def _mix_rgb(
    a: tuple[int, int, int],
    b: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:
    amount = max(0.0, min(1.0, amount))

    return tuple(
        round(x + (y - x) * amount)
        for x, y in zip(a, b)
    )


def _relative_luminance(
    color: tuple[int, int, int],
) -> float:
    channels = []

    for channel in color:
        value = channel / 255

        if value <= 0.04045:
            value /= 12.92
        else:
            value = ((value + 0.055) / 1.055) ** 2.4

        channels.append(value)

    r, g, b = channels

    return (
        0.2126 * r
        + 0.7152 * g
        + 0.0722 * b
    )


def _contrast_ratio(
    a: tuple[int, int, int],
    b: tuple[int, int, int],
) -> float:
    a_lum = _relative_luminance(a)
    b_lum = _relative_luminance(b)

    lighter = max(a_lum, b_lum)
    darker = min(a_lum, b_lum)

    return (lighter + 0.05) / (darker + 0.05)


def _ensure_text_contrast(
    requested: tuple[int, int, int],
    background: tuple[int, int, int],
    minimum: float = 4.5,
) -> tuple[int, int, int]:
    """
    Keep the requested text colour if it is sufficiently readable.

    Otherwise use a safe near-white or near-black.
    """
    if _contrast_ratio(requested, background) >= minimum:
        return requested

    light = (248, 250, 252)
    dark = (17, 24, 39)

    if (
        _contrast_ratio(light, background)
        >= _contrast_ratio(dark, background)
    ):
        return light

    return dark


def _accent_from_background(
    background: tuple[int, int, int],
    seed: int,
) -> tuple[int, int, int]:
    """
    Generate an accent colour related to, but distinct from,
    the background colour.
    """
    r, g, b = (
        channel / 255
        for channel in background
    )

    hue, lightness, saturation = colorsys.rgb_to_hls(
        r,
        g,
        b,
    )

    hue_shift = (0.08, 0.16, 0.28, 0.42)[seed % 4]

    hue = (hue + hue_shift) % 1.0

    saturation = max(
        0.58,
        min(0.88, saturation + 0.15),
    )

    # Light accents on dark backgrounds,
    # darker accents on light backgrounds.
    lightness = 0.70 if lightness < 0.50 else 0.34

    r, g, b = colorsys.hls_to_rgb(
        hue,
        lightness,
        saturation,
    )

    return (
        round(r * 255),
        round(g * 255),
        round(b * 255),
    )


# ---------------------------------------------------------------------------
# Background design system
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ThumbnailPalette:
    """A curated, coordinated colour family: background stops plus a matching text and accent colour."""

    backgrounds: tuple[str, ...]
    text: str
    accent: str


_THUMBNAIL_PALETTES = [
    _ThumbnailPalette(
        backgrounds=("0b1120", "172554", "0369a1"),
        text="f8fafc",
        accent="38bdf8",
    ),
    _ThumbnailPalette(
        backgrounds=("17153b", "312e81", "7c3aed"),
        text="faf5ff",
        accent="c084fc",
    ),
    _ThumbnailPalette(
        backgrounds=("101827", "2b334d", "e85d45"),
        text="fffaf5",
        accent="fb923c",
    ),
    _ThumbnailPalette(
        backgrounds=("2a0f2f", "701a75", "db2777"),
        text="fdf4ff",
        accent="f9a8d4",
    ),
    _ThumbnailPalette(
        backgrounds=("052e2b", "065f46", "10b981"),
        text="ecfdf5",
        accent="6ee7b7",
    ),
    _ThumbnailPalette(
        backgrounds=("082f49", "155e75", "0891b2"),
        text="ecfeff",
        accent="67e8f9",
    ),
    _ThumbnailPalette(
        backgrounds=("3f0d22", "9f1239", "f97316"),
        text="fff7ed",
        accent="fbbf24",
    ),
    _ThumbnailPalette(
        backgrounds=("09090b", "18181b", "1d4ed8"),
        text="fafafa",
        accent="60a5fa",
    ),
    _ThumbnailPalette(
        backgrounds=("27170d", "78350f", "d97706"),
        text="fffbeb",
        accent="fcd34d",
    ),
    _ThumbnailPalette(
        backgrounds=("111827", "374151", "be123c"),
        text="f9fafb",
        accent="fb7185",
    ),
    _ThumbnailPalette(
        backgrounds=("ecfdf5", "a7f3d0", "67e8f9"),
        text="102a2a",
        accent="047857",
    ),
    _ThumbnailPalette(
        backgrounds=("fff7ed", "fed7aa", "fda4af"),
        text="431407",
        accent="c2410c",
    ),
    _ThumbnailPalette(
        backgrounds=("faf5ff", "ddd6fe", "c4b5fd"),
        text="2e1065",
        accent="6d28d9",
    ),
    _ThumbnailPalette(
        backgrounds=("fffbeb", "d1fae5", "99f6e4"),
        text="134e4a",
        accent="0f766e",
    ),
]

_BACKGROUND_TYPES = {
    "solid": 12,
    "linear_ab": 28,
    "linear_aba": 18,
    "linear_abc": 12,
    "radial": 18,
    "corner_glow": 12,
}

_BACKGROUND_COMPLEXITY = {
    "solid": 0,
    "linear_ab": 1,
    "linear_aba": 1,
    "linear_abc": 2,
    "radial": 1,
    "corner_glow": 2,
}

_PATTERN_STRENGTH_BY_COMPLEXITY = {0: 1.0, 1: 0.85, 2: 0.6}

_LINEAR_ANGLE_WEIGHTS = {
    90: 26,
    -90: 22,
    45: 14,
    -45: 12,
    135: 10,
    -135: 8,
    0: 5,
    180: 3,
}


def _choose_palette(style_seed: int) -> _ThumbnailPalette:
    return _THUMBNAIL_PALETTES[style_seed % len(_THUMBNAIL_PALETTES)]


def _synthetic_palette_from_background(
    background: tuple[int, int, int],
    seed: int,
) -> _ThumbnailPalette:
    """
    Build a coherent 3-stop family from a single manually-supplied
    `bg_color`, so an override still gets the richer background
    system instead of falling back to a flatter look.

    The supplied colour is always `backgrounds[0]` -- a manual
    override is read, not silently replaced. The accent is derived
    with `_accent_from_background` per the documented fallback rule
    for non-curated backgrounds.
    """
    r, g, b = (channel / 255 for channel in background)
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)

    hue_shift = (0.05, -0.06, 0.09, -0.10)[seed % 4]
    secondary_hue = (hue + hue_shift) % 1.0

    is_dark = lightness < 0.5
    secondary_lightness = (
        min(0.85, lightness + 0.16)
        if is_dark
        else max(0.15, lightness - 0.16)
    )
    secondary_saturation = max(0.45, min(0.85, saturation + 0.10))

    sr, sg, sb = colorsys.hls_to_rgb(
        secondary_hue,
        secondary_lightness,
        secondary_saturation,
    )
    secondary = (round(sr * 255), round(sg * 255), round(sb * 255))

    accent = _accent_from_background(background, seed)

    return _ThumbnailPalette(
        backgrounds=(
            _rgb_to_hex(background),
            _rgb_to_hex(secondary),
            _rgb_to_hex(accent),
        ),
        text="fefefe",
        accent=_rgb_to_hex(accent),
    )


def _choose_background_style(background_rng: random.Random) -> str:
    return _weighted_choice(_BACKGROUND_TYPES, background_rng)


def _pattern_strength(background_style: str) -> float:
    complexity = _BACKGROUND_COMPLEXITY.get(background_style, 0)
    return _PATTERN_STRENGTH_BY_COMPLEXITY.get(complexity, 1.0)


def _scale_layer_alpha(layer: PIL.Image.Image, factor: float) -> PIL.Image.Image:
    """Scale an RGBA layer's alpha channel, leaving already-full-strength layers untouched."""
    if factor >= 0.999:
        return layer

    r, g, b, a = layer.split()
    a = a.point(lambda value: round(value * factor))

    return PIL.Image.merge("RGBA", (r, g, b, a))


def _linear_gradient_layer(
    size: tuple[int, int],
    black: tuple[int, int, int],
    white: tuple[int, int, int],
    mid: tuple[int, int, int] | None,
    midpoint_fraction: float,
    angle: int,
) -> PIL.Image.Image:
    """
    A full-canvas linear gradient at the given angle, colourised
    black -> [mid ->] white via `ImageOps.colorize` on top of
    Pillow's own gradient primitive -- no per-pixel Python loop
    regardless of canvas size.

    The pre-rotation size is the exact bounding box of `size` rotated
    by `-angle` (the standard rotated-rectangle formula), not just a
    generously-oversized square: sizing it too large would still
    avoid clipping, but would under-span the black->white range for
    near-vertical/near-horizontal angles on a wide canvas -- the
    crop would only ever show a muted middle slice, never reaching
    either requested colour.
    """
    w, h = size
    theta = math.radians(angle)

    span_h = max(2, round(w * abs(math.sin(theta)) + h * abs(math.cos(theta))) + 4)
    span_w = max(2, round(w * abs(math.cos(theta)) + h * abs(math.sin(theta))) + 4)

    grad = PIL.Image.linear_gradient("L").resize((span_w, span_h))

    if angle:
        grad = grad.rotate(angle, resample=PIL.Image.BICUBIC, expand=True)

    left = (grad.width - w) // 2
    top = (grad.height - h) // 2
    grad = grad.crop((left, top, left + w, top + h))

    colored = PIL.ImageOps.colorize(
        grad,
        black=black,
        white=white,
        mid=mid,
        midpoint=round(midpoint_fraction * 255),
    )

    return colored.convert("RGBA")


def _create_solid_background(
    size: tuple[int, int],
    color: tuple[int, int, int],
) -> PIL.Image.Image:
    return PIL.Image.new("RGBA", size, (*color, 255))


def _create_linear_ab_background(
    size: tuple[int, int],
    color_a: tuple[int, int, int],
    color_b: tuple[int, int, int],
    background_rng: random.Random,
) -> PIL.Image.Image:
    """A -> B, a true two-colour gradient."""
    angle = _weighted_choice(_LINEAR_ANGLE_WEIGHTS, background_rng)
    return _linear_gradient_layer(size, color_a, color_b, None, 0.5, angle)


def _create_linear_aba_background(
    size: tuple[int, int],
    color_a: tuple[int, int, int],
    color_b: tuple[int, int, int],
    background_rng: random.Random,
) -> PIL.Image.Image:
    """A -> B -> A, with the midpoint nudged off-centre so it reads as deliberate rather than mechanical."""
    angle = _weighted_choice(_LINEAR_ANGLE_WEIGHTS, background_rng)
    midpoint = background_rng.uniform(0.35, 0.65)
    return _linear_gradient_layer(size, color_a, color_a, color_b, midpoint, angle)


def _create_linear_abc_background(
    size: tuple[int, int],
    color_a: tuple[int, int, int],
    color_b: tuple[int, int, int],
    color_c: tuple[int, int, int],
    background_rng: random.Random,
) -> PIL.Image.Image:
    """A -> B -> C across the palette's full three-stop range -- more colourful, so used less often."""
    angle = _weighted_choice(_LINEAR_ANGLE_WEIGHTS, background_rng)
    midpoint = background_rng.uniform(0.40, 0.60)
    return _linear_gradient_layer(size, color_a, color_c, color_b, midpoint, angle)


def _create_radial_background(
    size: tuple[int, int],
    color_a: tuple[int, int, int],
    color_b: tuple[int, int, int],
    background_rng: random.Random,
) -> PIL.Image.Image:
    """A broad radial bloom of `color_a` fading to `color_b`, off-centre rather than a small, obviously-circular spot."""
    w, h = size

    center_x = background_rng.uniform(0.15, 0.85) * w
    center_y = background_rng.uniform(0.10, 0.90) * h

    corners = ((0, 0), (w, 0), (0, h), (w, h))
    max_dist = max(
        ((center_x - x) ** 2 + (center_y - y) ** 2) ** 0.5
        for x, y in corners
    )

    diameter = max(2, round(max_dist * 1.5))

    grad = PIL.Image.radial_gradient("L").resize((diameter, diameter))
    colored = PIL.ImageOps.colorize(grad, black=color_a, white=color_b).convert("RGBA")

    canvas = PIL.Image.new("RGBA", size, (*color_b, 255))
    canvas.paste(
        colored,
        (round(center_x - diameter / 2), round(center_y - diameter / 2)),
    )

    return canvas


def _radial_color_layer(
    size: tuple[int, int],
    color: tuple[int, int, int],
    center_x: float,
    center_y: float,
    radius: float,
    peak_alpha: int,
) -> PIL.Image.Image:
    """A soft, transparent-edged circular wash of `color`, meant to be composited on top of a base rather than fill the canvas."""
    diameter = max(2, round(radius * 2))

    grad = PIL.Image.radial_gradient("L").resize((diameter, diameter))
    alpha = PIL.ImageOps.invert(grad).point(lambda value: round(value * peak_alpha / 255))

    patch = PIL.Image.new("RGBA", (diameter, diameter), (*color, 0))
    patch.putalpha(alpha)

    layer = PIL.Image.new("RGBA", size, (0, 0, 0, 0))
    layer.paste(
        patch,
        (round(center_x - diameter / 2), round(center_y - diameter / 2)),
        patch,
    )

    return layer


# Fractional (x, y) ranges a glow's centre is drawn from, deliberately
# allowed to extend past 0/1 so blooms sit partially off-canvas rather
# than reading as small, contained circles.
_CORNER_ZONES = {
    "top_left": ((-0.15, 0.30), (-0.15, 0.30)),
    "top_right": ((0.70, 1.15), (-0.15, 0.30)),
    "bottom_left": ((-0.15, 0.30), (0.70, 1.15)),
    "bottom_right": ((0.70, 1.15), (0.70, 1.15)),
}

_OPPOSITE_CORNER = {
    "top_left": "bottom_right",
    "top_right": "bottom_left",
    "bottom_left": "top_right",
    "bottom_right": "top_left",
}


def _choose_glow_corner(layout: str, background_rng: random.Random) -> str:
    """Left-aligned titles keep their own side calm, so the glow leans right; centred titles can use any corner."""
    if layout == "left":
        return background_rng.choice(("top_right", "bottom_right"))

    return background_rng.choice(tuple(_CORNER_ZONES))


def _create_corner_glow_background(
    size: tuple[int, int],
    base_color: tuple[int, int, int],
    bloom_colors: tuple[tuple[int, int, int], ...],
    layout: str,
    background_rng: random.Random,
) -> PIL.Image.Image:
    """
    A restrained base with one (commonly) or two (occasionally) large,
    soft colour blooms hanging partially off-canvas -- modern
    editorial/observability-dashboard territory, not a vignette.
    """
    w, h = size
    image = PIL.Image.new("RGBA", size, (*base_color, 255))

    zone = _choose_glow_corner(layout, background_rng)
    zones = [zone]

    if background_rng.random() < 0.3:
        zones.append(_OPPOSITE_CORNER[zone])

    for i, current_zone in enumerate(zones):
        (x_lo, x_hi), (y_lo, y_hi) = _CORNER_ZONES[current_zone]

        center_x = background_rng.uniform(x_lo, x_hi) * w
        center_y = background_rng.uniform(y_lo, y_hi) * h
        radius = background_rng.uniform(0.55, 0.90) * max(w, h)
        color = bloom_colors[i % len(bloom_colors)]
        peak_alpha = 205 if i == 0 else 165  # a second glow stays a touch more restrained

        glow = _radial_color_layer(size, color, center_x, center_y, radius, peak_alpha)
        image = PIL.Image.alpha_composite(image, glow)

    return image


def _create_background(
    size: tuple[int, int],
    palette: _ThumbnailPalette,
    background_style: str,
    layout: str,
    background_rng: random.Random,
) -> PIL.Image.Image:
    bg0, bg1, bg2 = (_hex_to_rgb(color) for color in palette.backgrounds)

    if background_style == "solid":
        return _create_solid_background(size, bg0)

    if background_style == "linear_ab":
        return _create_linear_ab_background(size, bg0, bg2, background_rng)

    if background_style == "linear_aba":
        return _create_linear_aba_background(size, bg0, bg1, background_rng)

    if background_style == "linear_abc":
        return _create_linear_abc_background(size, bg0, bg1, bg2, background_rng)

    if background_style == "radial":
        return _create_radial_background(size, bg0, bg2, background_rng)

    return _create_corner_glow_background(size, bg0, (bg2, bg1), layout, background_rng)


def _existing_fonts() -> list[Path]:
    fonts = [
        path
        for path in _FONT_PATHS
        if path.exists()
    ]

    if not fonts:
        raise FileNotFoundError(
            f"No thumbnail fonts found in {_FONTS_DIR}. "
            "Expected at least one TTF font."
        )

    return fonts


# ---------------------------------------------------------------------------
# Text layout
# ---------------------------------------------------------------------------


def _wrap_candidates(
    words: list[str],
    max_lines: int = 3,
):
    """
    Yield possible 1-3 line splits.

    Thumbnail titles are short enough that trying each possible
    split is cheap, and produces much nicer wrapping than textwrap.
    """
    if not words:
        yield [""]
        return

    # One line
    yield [" ".join(words)]

    # Two lines
    if max_lines >= 2:
        for i in range(1, len(words)):
            yield [
                " ".join(words[:i]),
                " ".join(words[i:]),
            ]

    # Three lines
    if max_lines >= 3:
        for i in range(1, len(words) - 1):
            for j in range(i + 1, len(words)):
                yield [
                    " ".join(words[:i]),
                    " ".join(words[i:j]),
                    " ".join(words[j:]),
                ]


def _fit_title(
    draw: PIL.ImageDraw.ImageDraw,
    title: str,
    font_path: Path,
    max_width: int,
    max_height: int,
    image_height: int,
    align: str,
) -> tuple[
    PIL.ImageFont.FreeTypeFont,
    str,
    int,
]:
    """
    Find the largest font size and the most balanced 1-3 line
    wrapping that fits the available region.

    This uses rendered pixel dimensions rather than character count.
    """
    words = title.split() or [title]

    if len(title) <= 18:
        max_font_size = int(image_height * 0.34)
    else:
        max_font_size = int(image_height * 0.28)

    min_font_size = max(
        22,
        int(image_height * 0.075),
    )

    for font_size in range(
        max_font_size,
        min_font_size - 1,
        -2,
    ):
        font = PIL.ImageFont.truetype(
            font_path.as_posix(),
            font_size,
        )

        spacing = max(
            4,
            round(font_size * 0.10),
        )

        fitting = []

        for lines in _wrap_candidates(
            words,
            max_lines=3,
        ):
            rendered = "\n".join(lines)

            bbox = draw.multiline_textbbox(
                (0, 0),
                rendered,
                font=font,
                spacing=spacing,
                align=align,
            )

            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]

            if width > max_width:
                continue

            if height > max_height:
                continue

            line_widths = [
                draw.textbbox(
                    (0, 0),
                    line,
                    font=font,
                )[2]
                for line in lines
            ]

            mean_width = (
                sum(line_widths)
                / len(line_widths)
            )

            raggedness = sum(
                abs(width - mean_width)
                for width in line_widths
            )

            # Balanced wrapping matters, but prefer fewer lines
            # slightly when two choices look similarly good.
            score = (
                raggedness
                + (len(lines) - 1)
                * max_width
                * 0.08
            )

            fitting.append(
                (score, rendered)
            )

        if fitting:
            _, rendered = min(
                fitting,
                key=lambda item: item[0],
            )

            return (
                font,
                rendered,
                spacing,
            )

    # Emergency fallback for a title containing one extremely
    # long word/token.
    font = PIL.ImageFont.truetype(
        font_path.as_posix(),
        min_font_size,
    )

    spacing = max(
        4,
        round(min_font_size * 0.10),
    )

    rendered = title

    while rendered:
        candidate = (
            rendered.rstrip()
            + ("..." if rendered != title else "")
        )

        bbox = draw.textbbox(
            (0, 0),
            candidate,
            font=font,
        )

        if bbox[2] - bbox[0] <= max_width:
            return (
                font,
                candidate,
                spacing,
            )

        rendered = rendered[:-1]

    return (
        font,
        "...",
        spacing,
    )


# ---------------------------------------------------------------------------
# Decorative patterns
# ---------------------------------------------------------------------------


def _draw_rings(
    draw,
    w,
    h,
    rng,
    accent,
):
    width = max(
        2,
        w // 220,
    )

    side = rng.choice(
        ("left", "right")
    )

    if side == "right":
        cx = int(w * 0.92)
    else:
        cx = int(w * 0.08)

    cy = rng.randint(
        int(h * 0.10),
        int(h * 0.90),
    )

    gap = rng.randint(
        max(24, h // 12),
        max(34, h // 8),
    )

    for i in range(1, 6):
        radius = i * gap

        alpha = max(
            18,
            90 - i * 12,
        )

        draw.ellipse(
            (
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
            ),
            outline=(
                *accent,
                alpha,
            ),
            width=width,
        )


def _draw_grid(
    draw,
    w,
    h,
    rng,
    accent,
):
    spacing = rng.randint(
        max(38, w // 24),
        max(52, w // 18),
    )

    alpha = rng.randint(
        20,
        32,
    )

    offset_x = rng.randint(
        0,
        spacing,
    )

    offset_y = rng.randint(
        0,
        spacing,
    )

    for x in range(
        offset_x,
        w,
        spacing,
    ):
        draw.line(
            (x, 0, x, h),
            fill=(
                *accent,
                alpha,
            ),
            width=1,
        )

    for y in range(
        offset_y,
        h,
        spacing,
    ):
        draw.line(
            (0, y, w, y),
            fill=(
                *accent,
                alpha,
            ),
            width=1,
        )

    # A few stronger points make the grid look intentional
    # rather than like plain graph paper.
    for _ in range(
        rng.randint(4, 8)
    ):
        x = rng.randrange(
            offset_x,
            max(offset_x + 1, w),
            spacing,
        )

        y = rng.randrange(
            offset_y,
            max(offset_y + 1, h),
            spacing,
        )

        radius = max(
            3,
            min(w, h) // 120,
        )

        draw.ellipse(
            (
                x - radius,
                y - radius,
                x + radius,
                y + radius,
            ),
            fill=(
                *accent,
                90,
            ),
        )


def _draw_diagonal_blocks(
    draw,
    w,
    h,
    rng,
    accent,
):
    direction = rng.choice(
        (-1, 1)
    )

    band_w = rng.randint(
        max(70, w // 10),
        max(110, w // 6),
    )

    x = rng.choice(
        (
            int(w * 0.78),
            int(w * 0.08),
        )
    )

    for i in range(3):
        offset = i * int(
            band_w * 0.55
        )

        alpha = 45 - i * 8

        if direction > 0:
            points = [
                (
                    x + offset,
                    -h * 0.15,
                ),
                (
                    x + band_w + offset,
                    -h * 0.15,
                ),
                (
                    x + offset,
                    h * 1.15,
                ),
                (
                    x - band_w + offset,
                    h * 1.15,
                ),
            ]

        else:
            points = [
                (
                    x + offset,
                    -h * 0.15,
                ),
                (
                    x + band_w + offset,
                    -h * 0.15,
                ),
                (
                    x + band_w * 2 + offset,
                    h * 1.15,
                ),
                (
                    x + band_w + offset,
                    h * 1.15,
                ),
            ]

        draw.polygon(
            points,
            fill=(
                *accent,
                alpha,
            ),
        )


def _draw_dot_cluster(
    draw,
    w,
    h,
    rng,
    accent,
):
    columns = rng.randint(
        7,
        11,
    )

    rows = rng.randint(
        5,
        8,
    )

    side = rng.choice(
        ("left", "right")
    )

    area_w = int(
        w * 0.28
    )

    area_h = int(
        h * 0.65
    )

    if side == "left":
        start_x = 0
    else:
        start_x = w - area_w

    start_y = rng.randint(
        0,
        max(0, h - area_h),
    )

    cell_w = (
        area_w
        / columns
    )

    cell_h = (
        area_h
        / rows
    )

    for col in range(columns):
        for row in range(rows):
            cx = (
                start_x
                + cell_w
                * (col + 0.5)
            )

            cy = (
                start_y
                + cell_h
                * (row + 0.5)
            )

            progression = (
                col
                / max(
                    1,
                    columns - 1,
                )
            )

            if side == "right":
                progression = (
                    1 - progression
                )

            radius = max(
                2,
                min(
                    cell_w,
                    cell_h,
                )
                * (
                    0.08
                    + progression * 0.15
                ),
            )

            draw.ellipse(
                (
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                ),
                fill=(
                    *accent,
                    55,
                ),
            )


def _draw_waves(
    draw,
    w,
    h,
    rng,
    accent,
):
    count = rng.randint(
        3,
        5,
    )

    baseline = rng.choice(
        (
            int(h * 0.20),
            int(h * 0.78),
        )
    )

    for i in range(count):
        amplitude = rng.randint(
            max(10, h // 30),
            max(18, h // 16),
        )

        frequency = rng.uniform(
            0.006,
            0.012,
        )

        phase = rng.uniform(
            0,
            math.tau,
        )

        y_base = (
            baseline
            + i
            * max(
                8,
                h // 40,
            )
        )

        points = [
            (
                x,
                y_base
                + amplitude
                * math.sin(
                    frequency * x
                    + phase
                ),
            )
            for x in range(
                0,
                w + 1,
                max(
                    3,
                    w // 300,
                ),
            )
        ]

        draw.line(
            points,
            fill=(
                *accent,
                max(
                    24,
                    65 - i * 8,
                ),
            ),
            width=max(
                2,
                w // 350,
            ),
        )


def _draw_corner_geometry(
    draw,
    w,
    h,
    rng,
    accent,
):
    corners = [
        (0, 0, 1, 1),
        (w, 0, -1, 1),
        (0, h, 1, -1),
        (w, h, -1, -1),
    ]

    rng.shuffle(corners)

    for cx, cy, sx, sy in corners[:2]:
        size = rng.randint(
            int(
                min(w, h)
                * 0.14
            ),
            int(
                min(w, h)
                * 0.26
            ),
        )

        inset = size // 3

        x2 = cx + sx * size
        y2 = cy + sy * size

        draw.rounded_rectangle(
            (
                min(cx, x2),
                min(cy, y2),
                max(cx, x2),
                max(cy, y2),
            ),
            radius=max(
                8,
                size // 8,
            ),
            outline=(
                *accent,
                75,
            ),
            width=max(
                2,
                w // 250,
            ),
        )

        draw.line(
            (
                cx,
                cy + sy * inset,
                cx + sx * (size - inset),
                cy + sy * size,
            ),
            fill=(
                *accent,
                42,
            ),
            width=max(
                2,
                w // 300,
            ),
        )


_PATTERN_FUNCS = [
    _draw_rings,
    _draw_grid,
    _draw_diagonal_blocks,
    _draw_dot_cluster,
    _draw_waves,
    _draw_corner_geometry,
]


# ---------------------------------------------------------------------------
# Text effects
# ---------------------------------------------------------------------------


@dataclass
class _TitleLayout:
    """Everything an effect needs to (re)draw the already-fitted title."""

    font: PIL.ImageFont.FreeTypeFont
    rendered_text: str
    spacing: int
    align: str
    text_x: int
    text_y: int
    text_bbox: tuple[int, int, int, int]

    @property
    def lines(self) -> list[str]:
        return self.rendered_text.split("\n")


@dataclass
class _TextEffectContext:
    """
    What the effect scorers see: the actual fitted/rendered context,
    not just the seed. Built once per thumbnail, after the title has
    been fitted and the decorative pattern rendered, so scoring
    reflects the real composition instead of guessing from inputs
    like font family or flat background colour alone.
    """

    layout: str
    font_path: Path
    font_size: int
    font_size_ratio: float  # font_size / h -- how large the type reads

    line_count: int
    word_count: int

    text_width_ratio: float
    text_height_ratio: float

    background_luminance: float
    local_background_luminance: float
    local_background_variance: float
    minimum_text_contrast: float

    accent_background_contrast: float
    accent_text_contrast: float

    pattern_density: float


_CONDENSED_FONT_STEMS = {
    "BarlowCondensed-SemiBold",
    "Oswald-Bold",
    "FjallaOne-Regular",
}

_HEAVY_DISPLAY_FONT_STEMS = {
    "ArchivoBlack-Regular",
    "Anton-Regular",
    "Sora-ExtraBold",
    "LeagueSpartan-Bold",
}

_TECH_FONT_STEMS = {
    "SpaceGrotesk-Bold",
    "Oxanium-Bold",
    "Rajdhani-Bold",
}

_SHADOW_COLOR = (8, 9, 12)

_SHORT_STOPWORDS = {
    # Norwegian
    "og", "i", "på", "av", "en", "et", "er", "til", "for", "med",
    "som", "de", "det", "den", "du", "vi", "å", "om", "ikke", "har",
    # English
    "a", "an", "the", "of", "to", "in", "on", "at", "is", "it",
    "and", "or", "as", "by", "be", "are", "was",
}


def _clean_word(word: str) -> str:
    return word.strip(".,:;!?()[]{}'\"«»“”‘’-–—").lower()


def _select_accent_word_index(
    words: list[str],
    effect_rng: random.Random,
) -> int | None:
    """
    Pick a word to highlight in the accent colour.

    Short grammatical words (articles, prepositions, conjunctions)
    make weak, hard-to-read accents, so they're filtered out first.
    The fallback only relaxes the minimum length -- never the
    stopword filter -- and gives up if nothing qualifies, so callers
    can fall back to a different effect entirely.
    """

    def candidates(min_length: int) -> list[int]:
        return [
            i
            for i, word in enumerate(words)
            if len(_clean_word(word)) >= min_length
            and _clean_word(word) not in _SHORT_STOPWORDS
        ]

    picks = candidates(4) or candidates(3)

    return effect_rng.choice(picks) if picks else None


def _analyze_text_background(
    image: PIL.Image.Image,
    decoration: PIL.Image.Image,
    box: tuple[int, int, int, int],
    text: tuple[int, int, int],
    w: int,
    h: int,
    cols: int = 6,
    rows: int = 3,
) -> tuple[float, float, float, float]:
    """
    Sample a small grid across the title's region on the already
    composited (gradient + pattern) image, to see what's actually
    behind the glyphs instead of assuming the flat background colour.

    Returns (avg_luminance, luminance_range, min_contrast,
    pattern_density). `luminance_range` doubles as a cheap busyness
    proxy; `min_contrast` is the worst-case text/background contrast
    under the glyphs, which is what actually threatens legibility.
    `pattern_density` reads the decoration layer's own alpha (rather
    than the composited pixels) so a plain gradient -- which already
    shows up in the luminance range -- doesn't get counted twice as
    "decoration nearby".

    18 samples is enough signal for a thumbnail-sized decision and
    stays cheap even though this runs on every generated thumbnail.
    """
    left, top, right, bottom = box
    pad_x = max(4, round((right - left) * 0.08))
    pad_y = max(4, round((bottom - top) * 0.15))

    left = max(0, left - pad_x)
    top = max(0, top - pad_y)
    right = min(w, right + pad_x)
    bottom = min(h, bottom + pad_y)

    rgb_pixels = image.convert("RGB").load()
    alpha_pixels = decoration.getchannel("A").load()

    luminances = []
    alphas = []
    min_contrast = float("inf")

    for row in range(rows):
        for col in range(cols):
            x = min(w - 1, max(0, int(left + (right - left) * (col + 0.5) / cols)))
            y = min(h - 1, max(0, int(top + (bottom - top) * (row + 0.5) / rows)))

            sample = rgb_pixels[x, y]
            luminances.append(_relative_luminance(sample))
            min_contrast = min(min_contrast, _contrast_ratio(text, sample))
            alphas.append(alpha_pixels[x, y])

    avg_luminance = sum(luminances) / len(luminances)
    luminance_range = max(luminances) - min(luminances)
    pattern_density = (sum(alphas) / len(alphas)) / 255

    return avg_luminance, luminance_range, min_contrast, pattern_density


def _build_text_effect_context(
    *,
    layout: str,
    font_path: Path,
    font: PIL.ImageFont.FreeTypeFont,
    words: list[str],
    rendered_text: str,
    text_w: int,
    text_h: int,
    w: int,
    h: int,
    background: tuple[int, int, int],
    text: tuple[int, int, int],
    accent: tuple[int, int, int],
    local_luminance: float,
    local_variance: float,
    local_min_contrast: float,
    pattern_density: float,
) -> _TextEffectContext:
    return _TextEffectContext(
        layout=layout,
        font_path=font_path,
        font_size=font.size,
        font_size_ratio=font.size / h,
        line_count=rendered_text.count("\n") + 1,
        word_count=len(words),
        text_width_ratio=text_w / w,
        text_height_ratio=text_h / h,
        background_luminance=_relative_luminance(background),
        local_background_luminance=local_luminance,
        local_background_variance=local_variance,
        minimum_text_contrast=local_min_contrast,
        accent_background_contrast=_contrast_ratio(accent, background),
        accent_text_contrast=_contrast_ratio(accent, text),
        pattern_density=pattern_density,
    )


# ---------------------------------------------------------------------------
# Effect scoring
# ---------------------------------------------------------------------------


def _score_no_isolation(ctx: _TextEffectContext) -> float:
    """Baseline for "the title is already fine as-is", so a clean/high-contrast region can beat every real treatment."""
    score = 2.0

    if ctx.minimum_text_contrast >= 6.5 and ctx.local_background_variance < 0.05:
        score += 4.0
    elif ctx.minimum_text_contrast >= 5.0 and ctx.local_background_variance < 0.08:
        score += 2.0

    return score


def _score_shadow(ctx: _TextEffectContext) -> float:
    """
    Shadow is for lifting the title off a moderately busy background
    -- not a default. It backs off once the background is already
    clean (nothing to separate from) and needs at least a medium
    font size to read as intentional rather than mud.
    """
    if ctx.font_size_ratio < 0.10:
        return 0.0

    score = 2.0

    if 0.03 <= ctx.local_background_variance <= 0.22:
        score += 3.0
    elif ctx.local_background_variance > 0.22:
        score += 1.0  # still helps, but stroke/highlight usually fit a background this varied better

    if 3.5 <= ctx.minimum_text_contrast <= 7.0:
        score += 2.0

    score += ctx.pattern_density * 3.0

    if ctx.font_size_ratio >= 0.18:
        score += 1.0

    if ctx.minimum_text_contrast >= 8.0 and ctx.local_background_variance < 0.03:
        score *= 0.3

    return max(0.0, score)


def _score_stroke(ctx: _TextEffectContext) -> float:
    """
    A thin outline earns its place when the background genuinely
    crosses tones under the title (so glyph edges dip in and out of
    contrast) -- not just because the background is busy in general.
    """
    if ctx.font_size_ratio < 0.12:
        return 0.0

    if ctx.font_path.stem in _CONDENSED_FONT_STEMS and ctx.font_size_ratio < 0.20:
        return 0.0  # a thin stroke disappears into a narrow, small face

    score = 1.0

    if ctx.local_background_variance >= 0.18:
        score += 4.0
    elif ctx.local_background_variance >= 0.10:
        score += 2.0

    if ctx.minimum_text_contrast < 4.5:
        score += 2.0  # the actual problem case: contrast dips somewhere under the glyphs

    if ctx.local_background_variance < 0.04:
        score *= 0.25  # nothing for an outline to separate from

    return max(0.0, score)


def _score_highlight(ctx: _TextEffectContext) -> float:
    """
    The highlight panel is a readability fallback, not an ordinary
    random pick -- it should only compete once plain text genuinely
    can't stay reliably readable, or the backdrop is too chaotic for
    a shadow/stroke to fix.
    """
    score = 0.0

    if ctx.minimum_text_contrast < 3.5:
        score += 5.0

    if ctx.local_background_variance >= 0.28:
        score += 4.0

    if ctx.pattern_density >= 0.35:
        score += 2.0

    if ctx.line_count >= 3 and ctx.local_background_variance >= 0.15:
        score += 1.5  # occasional editorial card for a busy, chunky title

    return score


def _score_no_style(ctx: _TextEffectContext) -> float:
    """Baseline for "no stylistic flourish", so restraint stays the common outcome."""
    score = 6.0

    if ctx.line_count >= 3:
        score += 3.0

    if ctx.font_size_ratio < 0.14:
        score += 2.0

    if ctx.text_height_ratio > 0.75:
        score += 1.5  # the title already fills most of the frame; let it breathe

    return score


def _score_accent_word(ctx: _TextEffectContext, has_candidate: bool) -> float:
    """
    Recolouring a word is only worth it when there's a meaningful
    candidate (see `_select_accent_word_index`) AND the accent colour
    actually reads against the background it'll sit on -- otherwise
    the "highlighted" word just quietly disappears.
    """
    if not has_candidate:
        return 0.0

    if ctx.accent_background_contrast < 3.0:
        return 0.0

    if ctx.local_background_variance > 0.20:
        return 0.0  # too varied to trust one accent-coloured word to stay legible

    score = 3.0

    if 2 <= ctx.word_count <= 5:
        score += 2.5
    elif ctx.word_count > 8:
        score -= 2.0

    if ctx.line_count <= 2:
        score += 2.0
    else:
        score -= 1.5

    if ctx.layout == "center":
        score += 1.0

    if ctx.accent_background_contrast >= 4.5:
        score += 1.5

    return max(0.0, score)


def _score_offset(ctx: _TextEffectContext) -> float:
    """Display-typography effect: wants a bold face, real size, and a clean, roomy backdrop to duplicate against."""
    if ctx.font_path.stem in _CONDENSED_FONT_STEMS:
        return 0.0

    if ctx.font_size_ratio < 0.16:
        return 0.0

    if ctx.line_count >= 3:
        return 0.0

    score = 1.5

    if ctx.font_path.stem in _HEAVY_DISPLAY_FONT_STEMS:
        score += 3.0

    if ctx.font_size_ratio >= 0.24:
        score += 2.0

    if ctx.local_background_variance < 0.10:
        score += 2.0
    else:
        score -= 1.5

    if ctx.accent_background_contrast >= 4.0:
        score += 1.5

    if ctx.text_width_ratio > 0.86:
        score -= 1.5  # no room left for a duplicate to sit beside the glyphs

    return max(0.0, score)


def _score_glow(ctx: _TextEffectContext) -> float:
    """
    Glow is a stylistic effect, not a readability fix -- it wants a
    dark, clean patch behind large text and a genuinely bright
    accent, and should stay uncommon even when those line up.
    """
    if ctx.local_background_luminance >= 0.45:
        return 0.0  # glow reads as a smudge on a light backdrop

    if ctx.font_size_ratio < 0.16:
        return 0.0

    if ctx.line_count >= 3:
        return 0.0

    score = 1.0

    if ctx.local_background_variance < 0.10:
        score += 2.0
    else:
        score -= 1.5

    if ctx.accent_background_contrast >= 4.5:
        score += 2.0

    if ctx.font_path.stem in _TECH_FONT_STEMS:
        score += 1.5

    if ctx.line_count == 1:
        score += 1.0

    if ctx.font_size_ratio >= 0.24:
        score += 1.0

    return max(0.0, score)


def _score_gradient(ctx: _TextEffectContext) -> float:
    """Needs a settled backdrop and enough size/weight that the fill reads as deliberate rather than a rendering glitch."""
    if ctx.font_size_ratio < 0.18:
        return 0.0

    if ctx.line_count >= 3:
        return 0.0

    if ctx.font_path.stem in _CONDENSED_FONT_STEMS:
        return 0.0

    if ctx.local_background_variance > 0.16:
        return 0.0

    score = 1.0

    if ctx.accent_text_contrast >= 2.0:
        score += 1.5

    if ctx.font_size_ratio >= 0.24:
        score += 1.0

    if ctx.line_count == 1:
        score += 0.5

    return max(0.0, score)


def _score_extrude(ctx: _TextEffectContext) -> float:
    """
    Kept deliberately rare: every condition (heavy face, very large,
    one line, clean backdrop, strong accent, room to breathe) has to
    hold, or this scores exactly 0.
    """
    if ctx.font_path.stem not in _HEAVY_DISPLAY_FONT_STEMS:
        return 0.0

    if ctx.font_size_ratio < 0.26:
        return 0.0

    if ctx.line_count > 1:
        return 0.0

    if ctx.local_background_variance > 0.08:
        return 0.0

    if ctx.accent_background_contrast < 4.0:
        return 0.0

    if ctx.text_width_ratio > 0.80:
        return 0.0

    return 1.0


def _choose_isolation_treatment(
    ctx: _TextEffectContext,
    effect_rng: random.Random,
) -> str:
    """The readability layer: does this title need help separating from its background, and if so, how?"""
    scores = {
        "none": _score_no_isolation(ctx),
        "shadow": _score_shadow(ctx),
        "stroke": _score_stroke(ctx),
        "highlight": _score_highlight(ctx),
    }

    return _weighted_choice(scores, effect_rng)


def _choose_text_effect(
    ctx: _TextEffectContext,
    effect_rng: random.Random,
    has_accent_word: bool,
) -> str:
    """The stylistic layer: would a display-typography flourish suit this composition?"""
    scores = {
        "none": _score_no_style(ctx),
        "accent_word": _score_accent_word(ctx, has_accent_word),
        "offset": _score_offset(ctx),
        "glow": _score_glow(ctx),
        "gradient": _score_gradient(ctx),
        "extrude": _score_extrude(ctx),
    }

    return _weighted_choice(scores, effect_rng)


_SELF_CONTAINED_STYLES = {"accent_word", "gradient"}


def _reconcile_effects(isolation: str, stylistic: str) -> tuple[str, str]:
    """
    Resolve mechanical/visual conflicts between the independently
    chosen isolation treatment and stylistic effect.

    A highlight panel already recolours the whole area behind the
    title with `accent`, and every stylistic effect also draws in
    `accent` -- so pairing them would mean the "effect" blending
    straight into its own backdrop. Highlight is treated as a
    standalone composition choice instead (this also matches it
    being a readability fallback, not a flourish to stack things
    onto). A thin stroke and a self-contained stylistic effect
    (accent_word, gradient) both want to own the final glyph draw,
    so stroke steps aside when one of those is active.
    """
    if isolation == "highlight":
        return isolation, "none"

    if isolation == "stroke" and stylistic in _SELF_CONTAINED_STYLES:
        return "none", stylistic

    return isolation, stylistic


def _quiet_panel_alpha(ctx: _TextEffectContext) -> int:
    """
    How much the background needs calming immediately behind the
    title, as an alpha value rather than the old fixed 105.

    A clean, high-contrast region gets no panel at all; a busy or
    low-contrast one gets a stronger (but still restrained) one.
    Continuous rather than on/off so most thumbnails land somewhere
    in between instead of always looking like text on a card.
    """
    if ctx.minimum_text_contrast >= 7.0 and ctx.local_background_variance < 0.04:
        return 0

    strength = min(1.0, ctx.local_background_variance / 0.30) * 0.6
    strength += min(1.0, ctx.pattern_density) * 0.4

    if ctx.minimum_text_contrast < 4.5:
        strength = max(strength, 0.55)

    strength = min(1.0, strength)

    return round(35 + strength * 100)


def _line_positions(
    draw: PIL.ImageDraw.ImageDraw,
    lines: list[str],
    font: PIL.ImageFont.FreeTypeFont,
    spacing: int,
    align: str,
    x: float,
    y: float,
) -> list[tuple[float, float]]:
    """
    The (left, top) draw anchor Pillow itself would use for each line.

    This mirrors Pillow's own multiline layout (a fixed per-font line
    height, the same per-line alignment shift) using real
    measurements, so effects can target individual lines/words
    accurately instead of approximating from character counts.
    """
    line_height = draw.textbbox((0, 0), "A", font=font)[3] + spacing
    widths = [draw.textlength(line, font=font) for line in lines]
    max_width = max(widths, default=0)

    positions = []
    top = y

    for line, width in zip(lines, widths):
        left = x + (max_width - width) / 2 if align == "center" else x
        positions.append((left, top))
        top += line_height

    return positions


def _draw_text_plain(
    draw: PIL.ImageDraw.ImageDraw,
    layout: _TitleLayout,
    text: tuple[int, int, int],
    background: tuple[int, int, int],
) -> None:
    """
    Baseline treatment: a hairline stroke matched to the background
    colour, which smooths glyph edges against decorative patterns
    without reading as a deliberate outline.
    """
    stroke_width = max(1, layout.font.size // 48)

    draw.multiline_text(
        (layout.text_x, layout.text_y),
        layout.rendered_text,
        font=layout.font,
        fill=(*text, 255),
        spacing=layout.spacing,
        align=layout.align,
        stroke_width=stroke_width,
        stroke_fill=(*background, 225),
    )


def _stroke_color_for(
    text: tuple[int, int, int],
    background: tuple[int, int, int],
) -> tuple[int, int, int]:
    """The near-white/near-black that reads best against both the fill and whatever's behind it."""
    light = (250, 250, 252)
    dark = (15, 17, 20)

    light_score = min(
        _contrast_ratio(light, text),
        _contrast_ratio(light, background),
    )
    dark_score = min(
        _contrast_ratio(dark, text),
        _contrast_ratio(dark, background),
    )

    return light if light_score >= dark_score else dark


def _draw_text_stroke(
    draw: PIL.ImageDraw.ImageDraw,
    layout: _TitleLayout,
    text: tuple[int, int, int],
    background: tuple[int, int, int],
) -> None:
    """A thin, deliberate outline -- never the thick meme-text look."""
    stroke_width = max(1, round(layout.font.size * 0.022))
    stroke_color = _stroke_color_for(text, background)

    draw.multiline_text(
        (layout.text_x, layout.text_y),
        layout.rendered_text,
        font=layout.font,
        fill=(*text, 255),
        spacing=layout.spacing,
        align=layout.align,
        stroke_width=stroke_width,
        stroke_fill=(*stroke_color, 235),
    )


def _draw_text_shadow(
    image: PIL.Image.Image,
    layout: _TitleLayout,
    w: int,
    h: int,
    color: tuple[int, int, int] = _SHADOW_COLOR,
    opacity: int = 95,
) -> PIL.Image.Image:
    """
    A soft, low-opacity shadow offset a few pixels down-right and
    lightly blurred -- meant to lift the title off a busy background,
    not to read as a heavy drop shadow.
    """
    font_size = layout.font.size
    dx = max(1, round(font_size * 0.035))
    dy = max(2, round(font_size * 0.05))
    blur = max(1.0, font_size * 0.03)

    shadow = PIL.Image.new("RGBA", (w, h), (0, 0, 0, 0))

    PIL.ImageDraw.Draw(shadow).multiline_text(
        (layout.text_x + dx, layout.text_y + dy),
        layout.rendered_text,
        font=layout.font,
        fill=(*color, opacity),
        spacing=layout.spacing,
        align=layout.align,
    )

    shadow = shadow.filter(PIL.ImageFilter.GaussianBlur(blur))

    return PIL.Image.alpha_composite(image, shadow)


def _draw_text_glow(
    image: PIL.Image.Image,
    layout: _TitleLayout,
    w: int,
    h: int,
    glow_color: tuple[int, int, int],
    opacity: int = 80,
) -> PIL.Image.Image:
    """A blurred, centred halo behind the (still crisp) foreground text."""
    blur = max(3.0, layout.font.size * 0.11)

    glow = PIL.Image.new("RGBA", (w, h), (0, 0, 0, 0))

    PIL.ImageDraw.Draw(glow).multiline_text(
        (layout.text_x, layout.text_y),
        layout.rendered_text,
        font=layout.font,
        fill=(*glow_color, opacity),
        spacing=layout.spacing,
        align=layout.align,
    )

    glow = glow.filter(PIL.ImageFilter.GaussianBlur(blur))

    return PIL.Image.alpha_composite(image, glow)


def _draw_text_offset(
    image: PIL.Image.Image,
    layout: _TitleLayout,
    w: int,
    h: int,
    accent: tuple[int, int, int],
    effect_rng: random.Random,
) -> PIL.Image.Image:
    """A second, accent-coloured copy a few pixels behind the title -- restrained, not a big displacement."""
    magnitude = max(3, round(layout.font.size * 0.06))
    dx = effect_rng.choice((-1, 1)) * magnitude
    dy = magnitude

    duplicate = PIL.Image.new("RGBA", (w, h), (0, 0, 0, 0))

    PIL.ImageDraw.Draw(duplicate).multiline_text(
        (layout.text_x + dx, layout.text_y + dy),
        layout.rendered_text,
        font=layout.font,
        fill=(*accent, 235),
        spacing=layout.spacing,
        align=layout.align,
    )

    return PIL.Image.alpha_composite(image, duplicate)


def _draw_text_extrude(
    image: PIL.Image.Image,
    layout: _TitleLayout,
    w: int,
    h: int,
    accent: tuple[int, int, int],
) -> PIL.Image.Image:
    """
    Shallow pseudo-3D depth: a few 1px-stepped, progressively darker
    copies behind the foreground. Kept intentionally shallow so it
    reads like a printed poster's drop-repeat, not an arcade logo.
    """
    steps = 4
    layer = PIL.Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer_draw = PIL.ImageDraw.Draw(layer)

    for depth in range(steps, 0, -1):
        shade = _mix_rgb(accent, (0, 0, 0), 0.12 * depth)

        layer_draw.multiline_text(
            (layout.text_x + depth, layout.text_y + depth),
            layout.rendered_text,
            font=layout.font,
            fill=(*shade, 255),
            spacing=layout.spacing,
            align=layout.align,
        )

    return PIL.Image.alpha_composite(image, layer)


def _draw_highlight_block(
    image: PIL.Image.Image,
    w: int,
    h: int,
    text_bbox: tuple[int, int, int, int],
    text: tuple[int, int, int],
    accent: tuple[int, int, int],
    background: tuple[int, int, int],
) -> tuple[PIL.Image.Image, tuple[int, int, int]]:
    """
    A rounded accent panel behind the title, padded like an editorial
    caption card rather than a UI button. Replaces the default quiet
    panel for this effect (see `create_thumbnail`) so the two don't
    visually stack.

    Returns the composited image and a text colour guaranteed to
    read clearly against the panel.
    """
    pad_x = max(20, round(w * 0.028))
    pad_y = max(16, round(h * 0.05))

    box = (
        max(0, text_bbox[0] - pad_x),
        max(0, text_bbox[1] - pad_y),
        min(w, text_bbox[2] + pad_x),
        min(h, text_bbox[3] + pad_y),
    )

    layer = PIL.Image.new("RGBA", (w, h), (0, 0, 0, 0))

    PIL.ImageDraw.Draw(layer).rounded_rectangle(
        box,
        radius=max(10, h // 18),
        fill=(*accent, 235),
    )

    safe_text = _ensure_text_contrast(text, accent, minimum=4.5)

    return PIL.Image.alpha_composite(image, layer), safe_text


def _linear_text_fill(
    w: int,
    h: int,
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
    angle: float,
) -> PIL.Image.Image:
    """
    An oversized top-to-bottom gradient, optionally rotated a few
    degrees and cropped back to size. Rotating a vertical gradient is
    a cheap way to get a genuine diagonal linear gradient without a
    per-pixel Python loop over the whole canvas.
    """
    pad = round(max(w, h) * 0.4)
    grad_w = w + pad * 2
    grad_h = h + pad * 2

    gradient = PIL.Image.new("RGBA", (grad_w, grad_h), (0, 0, 0, 0))
    gradient_draw = PIL.ImageDraw.Draw(gradient)

    for y in range(grad_h):
        amount = y / max(1, grad_h - 1)

        gradient_draw.line(
            (0, y, grad_w, y),
            fill=(*_mix_rgb(top_color, bottom_color, amount), 255),
        )

    if angle:
        gradient = gradient.rotate(angle, resample=PIL.Image.BICUBIC)

    left = (gradient.width - w) // 2
    top = (gradient.height - h) // 2

    return gradient.crop((left, top, left + w, top + h))


def _draw_gradient_text(
    image: PIL.Image.Image,
    layout: _TitleLayout,
    w: int,
    h: int,
    text: tuple[int, int, int],
    accent: tuple[int, int, int],
    effect_rng: random.Random,
) -> PIL.Image.Image:
    """
    Fill the glyph shapes with a subtle gradient using a text mask,
    rather than rendering each character separately.

    The gradient stays close to `text`, blending only partway toward
    `accent`, so contrast stays close to the value already verified
    for the plain title colour instead of sweeping across the full
    accent hue.
    """
    mask = PIL.Image.new("L", (w, h), 0)

    PIL.ImageDraw.Draw(mask).multiline_text(
        (layout.text_x, layout.text_y),
        layout.rendered_text,
        font=layout.font,
        fill=255,
        spacing=layout.spacing,
        align=layout.align,
    )

    end_color = _mix_rgb(text, accent, 0.55)
    angle = effect_rng.choice((0, 0, -14, 14))

    fill = _linear_text_fill(w, h, text, end_color, angle)
    fill.putalpha(mask)

    return PIL.Image.alpha_composite(image, fill)


def _draw_accent_word(
    draw: PIL.ImageDraw.ImageDraw,
    layout: _TitleLayout,
    words: list[str],
    word_index: int,
    text: tuple[int, int, int],
    accent: tuple[int, int, int],
) -> bool:
    """
    Draw the title normally, then re-draw one word in the accent
    colour on top of itself.

    Uses real Pillow measurements (`_line_positions`, `textlength`)
    rather than character counts, so the recoloured word lines up
    correctly across wrapped lines and both layouts. Returns False
    (having drawn nothing) if the word can't be located -- e.g.
    `_fit_title` fell back to a truncated single-word render -- so
    the caller can fall back to a plain title instead.
    """
    lines = layout.lines
    target = words[word_index]

    counter = 0
    line_no = word_no = None
    line_words: list[str] = []

    for i, line in enumerate(lines):
        line_words = line.split(" ")

        if counter + len(line_words) > word_index:
            line_no = i
            word_no = word_index - counter
            break

        counter += len(line_words)

    if line_no is None or _clean_word(line_words[word_no]) != _clean_word(target):
        return False

    draw.multiline_text(
        (layout.text_x, layout.text_y),
        layout.rendered_text,
        font=layout.font,
        fill=(*text, 255),
        spacing=layout.spacing,
        align=layout.align,
    )

    line_left, line_top = _line_positions(
        draw,
        lines,
        layout.font,
        layout.spacing,
        layout.align,
        layout.text_x,
        layout.text_y,
    )[line_no]

    prefix = " ".join(line_words[:word_no])
    if word_no > 0:
        prefix += " "

    word_x = line_left + draw.textlength(prefix, font=layout.font)

    draw.text(
        (word_x, line_top),
        line_words[word_no],
        font=layout.font,
        fill=(*accent, 255),
    )

    return True


# ---------------------------------------------------------------------------
# Thumbnail renderer
# ---------------------------------------------------------------------------


@lru_cache_wrapper
def create_thumbnail(
    title: str,
    bg_color: str | None = None,
    text_color: str | None = None,
    size: tuple[int, int] = (800, 250),
    seed: str = "",
) -> PIL.Image.Image:
    """
    Create a deterministic fallback thumbnail.

    `seed` controls the visual style independently from the
    visible title.

    This means that `c` can later represent a module/category
    without requiring another rewrite of the renderer.

    `bg_color`/`text_color` are manual overrides (as `rrggbb` hex,
    no `#`); `api.py` is responsible for reading/sanitizing query
    params and passes `None` through when none was supplied. With no
    override, a curated `_ThumbnailPalette` supplies background,
    text, and accent colour as one coordinated family. With a manual
    `bg_color`, that colour becomes the base of a synthetic family
    (`_synthetic_palette_from_background`) instead -- the request is
    read, never silently replaced -- and the accent falls back to
    `_accent_from_background`.
    """
    w, h = size

    title = (
        " ".join(
            title.split()
        ).strip()
        or "Untitled"
    )

    style_seed = _seed_from_text(
        title,
        seed or title,
    )

    # Separate RNG streams per subsystem, so a change to one (e.g.
    # adding a background style) never reshuffles pattern placement
    # or text-effect choices for existing thumbnails.
    background_rng = random.Random(
        style_seed ^ 0xB4C6C0DE
    )

    pattern_rng = random.Random(
        style_seed ^ 0x9A11E4D9
    )

    if bg_color is not None:
        palette = _synthetic_palette_from_background(
            _hex_to_rgb(bg_color),
            style_seed,
        )
    else:
        palette = _choose_palette(
            style_seed
        )

    background = _hex_to_rgb(
        palette.backgrounds[0]
    )

    requested_text = _hex_to_rgb(
        text_color
        if text_color is not None
        else palette.text
    )

    # Guarantee readable typography.
    text = _ensure_text_contrast(
        requested_text,
        background,
    )

    accent = _hex_to_rgb(
        palette.accent
    )

    layout = (
        "center"
        if style_seed % 3
        else "left"
    )

    background_style = _choose_background_style(
        background_rng
    )

    image = _create_background(
        size,
        palette,
        background_style,
        layout,
        background_rng,
    )

    # ------------------------------------------------------------
    # Decorative pattern
    # ------------------------------------------------------------

    decoration = PIL.Image.new(
        "RGBA",
        size,
        (0, 0, 0, 0),
    )

    decoration_draw = (
        PIL.ImageDraw.Draw(
            decoration
        )
    )

    pattern_fn = _PATTERN_FUNCS[
        (style_seed // 7)
        % len(_PATTERN_FUNCS)
    ]

    pattern_fn(
        decoration_draw,
        w,
        h,
        pattern_rng,
        accent,
    )

    decoration = _scale_layer_alpha(
        decoration,
        _pattern_strength(background_style),
    )

    image = PIL.Image.alpha_composite(
        image,
        decoration,
    )

    measure_draw = PIL.ImageDraw.Draw(
        image
    )

    fonts = _existing_fonts()

    font_path = fonts[
        style_seed
        % len(fonts)
    ]

    if layout == "left":
        text_area_left = int(
            w * 0.10
        )

        text_area_right = int(
            w * 0.72
        )

        align = "left"

    else:
        text_area_left = int(
            w * 0.10
        )

        text_area_right = int(
            w * 0.90
        )

        align = "center"

    text_area_top = int(
        h * 0.12
    )

    text_area_bottom = int(
        h * 0.88
    )

    max_text_w = (
        text_area_right
        - text_area_left
    )

    max_text_h = (
        text_area_bottom
        - text_area_top
    )

    font, rendered_text, spacing = _fit_title(
        measure_draw,
        title,
        font_path,
        max_text_w,
        max_text_h,
        h,
        align,
    )

    local_bbox = (
        measure_draw.multiline_textbbox(
            (0, 0),
            rendered_text,
            font=font,
            spacing=spacing,
            align=align,
        )
    )

    text_w = (
        local_bbox[2]
        - local_bbox[0]
    )

    text_h = (
        local_bbox[3]
        - local_bbox[1]
    )

    if layout == "left":
        text_x = (
            text_area_left
            - local_bbox[0]
        )

    else:
        text_x = (
            (w - text_w) // 2
            - local_bbox[0]
        )

    text_y = (
        (h - text_h) // 2
        - local_bbox[1]
    )

    text_bbox = (
        measure_draw.multiline_textbbox(
            (text_x, text_y),
            rendered_text,
            font=font,
            spacing=spacing,
            align=align,
        )
    )

    # ------------------------------------------------------------
    # Effect selection
    # ------------------------------------------------------------

    words = title.split() or [title]

    local_luminance, local_variance, local_min_contrast, pattern_density = (
        _analyze_text_background(
            image,
            decoration,
            text_bbox,
            text,
            w,
            h,
        )
    )

    ctx = _build_text_effect_context(
        layout=layout,
        font_path=font_path,
        font=font,
        words=words,
        rendered_text=rendered_text,
        text_w=text_w,
        text_h=text_h,
        w=w,
        h=h,
        background=background,
        text=text,
        accent=accent,
        local_luminance=local_luminance,
        local_variance=local_variance,
        local_min_contrast=local_min_contrast,
        pattern_density=pattern_density,
    )

    effect_rng = random.Random(
        style_seed ^ 0x5A17C0DE
    )

    accent_word_index = _select_accent_word_index(
        words,
        effect_rng,
    )

    isolation = _choose_isolation_treatment(
        ctx,
        effect_rng,
    )

    text_effect = _choose_text_effect(
        ctx,
        effect_rng,
        accent_word_index is not None,
    )

    isolation, text_effect = _reconcile_effects(
        isolation,
        text_effect,
    )

    # ------------------------------------------------------------
    # Quiet area behind title
    # ------------------------------------------------------------

    if isolation != "highlight":
        quiet_alpha = _quiet_panel_alpha(ctx)

        if quiet_alpha > 0:
            quiet = PIL.Image.new(
                "RGBA",
                size,
                (0, 0, 0, 0),
            )

            quiet_draw = PIL.ImageDraw.Draw(
                quiet
            )

            panel_pad_x = max(
                18,
                w // 45,
            )

            panel_pad_y = max(
                14,
                h // 24,
            )

            panel_box = (
                max(
                    0,
                    text_bbox[0] - panel_pad_x,
                ),
                max(
                    0,
                    text_bbox[1] - panel_pad_y,
                ),
                min(
                    w,
                    text_bbox[2] + panel_pad_x,
                ),
                min(
                    h,
                    text_bbox[3] + panel_pad_y,
                ),
            )

            quiet_draw.rounded_rectangle(
                panel_box,
                radius=max(
                    12,
                    h // 20,
                ),
                fill=(
                    *background,
                    quiet_alpha,
                ),
            )

            image = PIL.Image.alpha_composite(
                image,
                quiet,
            )

    draw = PIL.ImageDraw.Draw(
        image
    )

    # ------------------------------------------------------------
    # Accent near title
    # ------------------------------------------------------------

    if isolation != "highlight":
        if layout == "left":
            bar_w = max(
                5,
                w // 170,
            )

            gap = max(
                14,
                w // 70,
            )

            draw.rounded_rectangle(
                (
                    text_bbox[0]
                    - gap
                    - bar_w,

                    text_bbox[1],

                    text_bbox[0]
                    - gap,

                    text_bbox[3],
                ),
                radius=bar_w,
                fill=(
                    *accent,
                    235,
                ),
            )

        else:
            underline_w = min(
                int(text_w * 0.28),
                int(w * 0.16),
            )

            underline_h = max(
                4,
                h // 85,
            )

            underline_y = min(
                h
                - underline_h
                - 12,

                text_bbox[3]
                + max(
                    14,
                    h // 24,
                ),
            )

            draw.rounded_rectangle(
                (
                    w // 2
                    - underline_w // 2,

                    underline_y,

                    w // 2
                    + underline_w // 2,

                    underline_y
                    + underline_h,
                ),
                radius=underline_h,
                fill=(
                    *accent,
                    235,
                ),
            )

    # ------------------------------------------------------------
    # Title
    # ------------------------------------------------------------

    title_layout = _TitleLayout(
        font=font,
        rendered_text=rendered_text,
        spacing=spacing,
        align=align,
        text_x=text_x,
        text_y=text_y,
        text_bbox=text_bbox,
    )

    foreground_color = text
    draw_foreground = True

    if isolation == "highlight":
        image, foreground_color = _draw_highlight_block(
            image,
            w,
            h,
            title_layout.text_bbox,
            text,
            accent,
            background,
        )

    if isolation == "shadow":
        image = _draw_text_shadow(image, title_layout, w, h)

    if text_effect == "glow":
        image = _draw_text_glow(image, title_layout, w, h, accent)
    elif text_effect == "offset":
        image = _draw_text_offset(image, title_layout, w, h, accent, effect_rng)
    elif text_effect == "extrude":
        image = _draw_text_extrude(image, title_layout, w, h, accent)

    draw = PIL.ImageDraw.Draw(image)

    if isolation == "stroke":
        _draw_text_stroke(draw, title_layout, foreground_color, background)
        draw_foreground = False

    elif text_effect == "accent_word" and accent_word_index is not None:
        placed = _draw_accent_word(
            draw,
            title_layout,
            words,
            accent_word_index,
            foreground_color,
            accent,
        )
        draw_foreground = not placed

    elif text_effect == "gradient":
        image = _draw_gradient_text(
            image,
            title_layout,
            w,
            h,
            foreground_color,
            accent,
            effect_rng,
        )
        draw_foreground = False

    if draw_foreground:
        _draw_text_plain(draw, title_layout, foreground_color, background)

    return image.convert("RGB")
