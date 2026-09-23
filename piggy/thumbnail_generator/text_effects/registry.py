"""Explicit registries for readability isolation and stylistic title effects."""

import random

from ..common import _weighted_choice
from .base import IsolationTreatment, TextEffectContext, TextStyle
from .isolation import HighlightIsolation, NoIsolation, ShadowIsolation, StrokeIsolation
from .styles import AccentWordStyle, ExtrudeStyle, GlowStyle, GradientStyle, NoTextStyle, OffsetStyle


# Keep order stable to preserve the original weighted-choice sequence.
ISOLATION_TREATMENTS: tuple[IsolationTreatment, ...] = (
    NoIsolation(),
    ShadowIsolation(),
    StrokeIsolation(),
    HighlightIsolation(),
)

TEXT_STYLES: tuple[TextStyle, ...] = (
    NoTextStyle(),
    AccentWordStyle(),
    OffsetStyle(),
    GlowStyle(),
    GradientStyle(),
    ExtrudeStyle(),
)

ISOLATIONS_BY_NAME = {effect.name: effect for effect in ISOLATION_TREATMENTS}
TEXT_STYLES_BY_NAME = {effect.name: effect for effect in TEXT_STYLES}


def choose_isolation_treatment(
    ctx: TextEffectContext,
    rng: random.Random,
) -> IsolationTreatment:
    scores = {effect.name: effect.score(ctx) for effect in ISOLATION_TREATMENTS}
    return ISOLATIONS_BY_NAME[_weighted_choice(scores, rng)]


def choose_text_style(
    ctx: TextEffectContext,
    rng: random.Random,
    has_accent_word: bool,
) -> TextStyle:
    scores = {effect.name: effect.score(ctx, has_accent_word) for effect in TEXT_STYLES}
    return TEXT_STYLES_BY_NAME[_weighted_choice(scores, rng)]


def reconcile_effects(
    isolation: IsolationTreatment,
    style: TextStyle,
) -> tuple[IsolationTreatment, TextStyle]:
    if isolation.suppresses_style:
        return isolation, TEXT_STYLES_BY_NAME["none"]

    if isolation.rejects_self_contained_style and style.self_contained:
        return ISOLATIONS_BY_NAME["none"], style

    return isolation, style
