"""Explicit background-style registry."""

import random

from ..common import _weighted_choice
from .base import BackgroundStyle
from .solid import SolidBackground
from .linear_ab import LinearABBackground
from .linear_aba import LinearABABackground
from .linear_abc import LinearABCBackground
from .radial import RadialBackground
from .corner_glow import CornerGlowBackground
from .helpers import PATTERN_STRENGTH_BY_COMPLEXITY


# Keep order stable to preserve the original weighted-choice sequence.
BACKGROUNDS: tuple[BackgroundStyle, ...] = (
    SolidBackground(),
    LinearABBackground(),
    LinearABABackground(),
    LinearABCBackground(),
    RadialBackground(),
    CornerGlowBackground(),
)

BACKGROUNDS_BY_NAME = {background.name: background for background in BACKGROUNDS}
BACKGROUND_TYPES = {background.name: background.weight for background in BACKGROUNDS}
BACKGROUND_COMPLEXITY = {background.name: background.complexity for background in BACKGROUNDS}


def choose_background_style(rng: random.Random) -> BackgroundStyle:
    name = _weighted_choice(BACKGROUND_TYPES, rng)
    return BACKGROUNDS_BY_NAME[name]


def pattern_strength(style: str | BackgroundStyle) -> float:
    complexity = style.complexity if isinstance(style, BackgroundStyle) else BACKGROUND_COMPLEXITY.get(style, 0)
    return PATTERN_STRENGTH_BY_COMPLEXITY.get(complexity, 1.0)
