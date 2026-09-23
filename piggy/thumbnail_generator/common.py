"""Shared deterministic, color, and contrast helpers for thumbnail generation."""

import colorsys
import random
from hashlib import md5

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
