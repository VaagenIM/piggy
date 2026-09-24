"""Object-oriented procedural thumbnail background system.

The underscore-prefixed names form a compatibility facade for existing
renderer/decals code. New code can use the class/registry API directly.
"""

import random

import PIL.Image

from .base import BackgroundContext, BackgroundStyle, ThumbnailPalette
from .helpers import (
    CORNER_ZONES,
    LINEAR_ANGLE_WEIGHTS,
    PATTERN_STRENGTH_BY_COMPLEXITY,
    radial_color_layer,
    scale_layer_alpha,
)
from .palette import THUMBNAIL_PALETTES, choose_palette, synthetic_palette_from_background
from .registry import (
    BACKGROUNDS,
    BACKGROUNDS_BY_NAME,
    BACKGROUND_COMPLEXITY,
    BACKGROUND_TYPES,
    choose_background_style,
    pattern_strength,
)

# Compatibility aliases from the previous procedural module.
_ThumbnailPalette = ThumbnailPalette
_THUMBNAIL_PALETTES = THUMBNAIL_PALETTES
_BACKGROUND_TYPES = BACKGROUND_TYPES
_BACKGROUND_COMPLEXITY = BACKGROUND_COMPLEXITY
_PATTERN_STRENGTH_BY_COMPLEXITY = PATTERN_STRENGTH_BY_COMPLEXITY
_LINEAR_ANGLE_WEIGHTS = LINEAR_ANGLE_WEIGHTS
_CORNER_ZONES = CORNER_ZONES
_radial_color_layer = radial_color_layer
_scale_layer_alpha = scale_layer_alpha


def _choose_palette(style_seed: int) -> ThumbnailPalette:
    return choose_palette(style_seed)


def _synthetic_palette_from_background(background, seed: int) -> ThumbnailPalette:
    return synthetic_palette_from_background(background, seed)


def _choose_background_style(background_rng: random.Random) -> str:
    return choose_background_style(background_rng).name


def _pattern_strength(background_style: str) -> float:
    return pattern_strength(background_style)


def _create_background(
    size: tuple[int, int],
    palette: ThumbnailPalette,
    background_style: str,
    layout: str,
    background_rng: random.Random,
) -> PIL.Image.Image:
    style = BACKGROUNDS_BY_NAME.get(background_style, BACKGROUNDS_BY_NAME["corner_glow"])
    return style.draw(
        BackgroundContext(
            size=size,
            palette=palette,
            layout=layout,
            rng=background_rng,
        )
    )


__all__ = [
    "BackgroundContext",
    "BackgroundStyle",
    "ThumbnailPalette",
    "BACKGROUNDS",
    "BACKGROUNDS_BY_NAME",
    "BACKGROUND_COMPLEXITY",
    "choose_background_style",
    "choose_palette",
    "synthetic_palette_from_background",
    "pattern_strength",
    "scale_layer_alpha",
    "_ThumbnailPalette",
    "_THUMBNAIL_PALETTES",
    "_BACKGROUND_TYPES",
    "_BACKGROUND_COMPLEXITY",
    "_CORNER_ZONES",
    "_radial_color_layer",
    "_choose_palette",
    "_synthetic_palette_from_background",
    "_choose_background_style",
    "_pattern_strength",
    "_scale_layer_alpha",
    "_create_background",
]
