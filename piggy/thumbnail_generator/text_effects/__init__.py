"""Object-oriented title effect system.

Isolation treatments and stylistic effects are independent objects with their
own scoring/rendering behaviour. Underscore-prefixed exports preserve the
previous procedural API while renderer.py can use the object API directly.
"""

import random

from .analysis import (
    analyze_text_background,
    build_text_effect_context,
    clean_word,
    quiet_panel_alpha,
    select_accent_word_index,
)
from .base import (
    IsolationTreatment,
    TextEffectContext,
    TextRenderContext,
    TextRenderState,
    TextStyle,
    TitleLayout,
)
from .helpers import draw_text_plain, line_positions, linear_text_fill
from .isolation import draw_highlight_block, draw_text_shadow, draw_text_stroke
from .registry import (
    ISOLATION_TREATMENTS,
    ISOLATIONS_BY_NAME,
    TEXT_STYLES,
    TEXT_STYLES_BY_NAME,
    choose_isolation_treatment,
    choose_text_style,
    reconcile_effects,
)
from .rendering import render_title
from .styles import (
    draw_accent_word,
    draw_gradient_text,
    draw_text_extrude,
    draw_text_glow,
    draw_text_offset,
)

# Compatibility aliases/types.
_TitleLayout = TitleLayout
_TextEffectContext = TextEffectContext
_clean_word = clean_word
_select_accent_word_index = select_accent_word_index
_analyze_text_background = analyze_text_background
_build_text_effect_context = build_text_effect_context
_quiet_panel_alpha = quiet_panel_alpha
_line_positions = line_positions
_draw_text_plain = draw_text_plain
_draw_text_shadow = draw_text_shadow
_draw_text_stroke = draw_text_stroke
_draw_highlight_block = draw_highlight_block
_draw_text_glow = draw_text_glow
_draw_text_offset = draw_text_offset
_draw_text_extrude = draw_text_extrude
_draw_gradient_text = draw_gradient_text
_draw_accent_word = draw_accent_word
_linear_text_fill = linear_text_fill


def _choose_isolation_treatment(ctx: TextEffectContext, effect_rng: random.Random) -> str:
    return choose_isolation_treatment(ctx, effect_rng).name


def _choose_text_effect(
    ctx: TextEffectContext,
    effect_rng: random.Random,
    has_accent_word: bool,
) -> str:
    return choose_text_style(ctx, effect_rng, has_accent_word).name


def _reconcile_effects(isolation: str, stylistic: str) -> tuple[str, str]:
    isolation_obj = ISOLATIONS_BY_NAME[isolation]
    style_obj = TEXT_STYLES_BY_NAME[stylistic]
    isolation_obj, style_obj = reconcile_effects(isolation_obj, style_obj)
    return isolation_obj.name, style_obj.name


__all__ = [
    "IsolationTreatment",
    "TextEffectContext",
    "TextRenderContext",
    "TextStyle",
    "TitleLayout",
    "ISOLATION_TREATMENTS",
    "TEXT_STYLES",
    "ISOLATIONS_BY_NAME",
    "TEXT_STYLES_BY_NAME",
    "choose_isolation_treatment",
    "choose_text_style",
    "reconcile_effects",
    "render_title",
    "analyze_text_background",
    "build_text_effect_context",
    "select_accent_word_index",
    "quiet_panel_alpha",
    "_TitleLayout",
    "_TextEffectContext",
    "_select_accent_word_index",
    "_analyze_text_background",
    "_build_text_effect_context",
    "_choose_isolation_treatment",
    "_choose_text_effect",
    "_reconcile_effects",
    "_quiet_panel_alpha",
    "_draw_text_plain",
    "_draw_text_shadow",
    "_draw_text_stroke",
    "_draw_highlight_block",
    "_draw_text_glow",
    "_draw_text_offset",
    "_draw_text_extrude",
    "_draw_gradient_text",
    "_draw_accent_word",
]
