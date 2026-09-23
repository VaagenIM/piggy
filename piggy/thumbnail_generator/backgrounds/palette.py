"""Curated and synthetic thumbnail palettes."""

import colorsys

from ..common import _accent_from_background, _rgb_to_hex
from .base import ThumbnailPalette


THUMBNAIL_PALETTES = [
    ThumbnailPalette(("0b1120", "172554", "0369a1"), "f8fafc", "38bdf8"),
    ThumbnailPalette(("17153b", "312e81", "7c3aed"), "faf5ff", "c084fc"),
    ThumbnailPalette(("101827", "2b334d", "e85d45"), "fffaf5", "fb923c"),
    ThumbnailPalette(("2a0f2f", "701a75", "db2777"), "fdf4ff", "f9a8d4"),
    ThumbnailPalette(("052e2b", "065f46", "10b981"), "ecfdf5", "6ee7b7"),
    ThumbnailPalette(("082f49", "155e75", "0891b2"), "ecfeff", "67e8f9"),
    ThumbnailPalette(("3f0d22", "9f1239", "f97316"), "fff7ed", "fbbf24"),
    ThumbnailPalette(("09090b", "18181b", "1d4ed8"), "fafafa", "60a5fa"),
    ThumbnailPalette(("27170d", "78350f", "d97706"), "fffbeb", "fcd34d"),
    ThumbnailPalette(("111827", "374151", "be123c"), "f9fafb", "fb7185"),
    ThumbnailPalette(("ecfdf5", "a7f3d0", "67e8f9"), "102a2a", "047857"),
    ThumbnailPalette(("fff7ed", "fed7aa", "fda4af"), "431407", "c2410c"),
    ThumbnailPalette(("faf5ff", "ddd6fe", "c4b5fd"), "2e1065", "6d28d9"),
    ThumbnailPalette(("fffbeb", "d1fae5", "99f6e4"), "134e4a", "0f766e"),
]


def choose_palette(style_seed: int) -> ThumbnailPalette:
    return THUMBNAIL_PALETTES[style_seed % len(THUMBNAIL_PALETTES)]


def synthetic_palette_from_background(
    background: tuple[int, int, int],
    seed: int,
) -> ThumbnailPalette:
    """Build a coherent three-stop family from a manual background colour."""
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

    return ThumbnailPalette(
        backgrounds=(
            _rgb_to_hex(background),
            _rgb_to_hex(secondary),
            _rgb_to_hex(accent),
        ),
        text="fefefe",
        accent=_rgb_to_hex(accent),
    )
