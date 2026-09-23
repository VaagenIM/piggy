import PIL.ImageDraw

from ...common import _contrast_ratio
from ..base import IsolationTreatment, TextEffectContext, TextRenderContext, TextRenderState, TitleLayout
from ..font_groups import CONDENSED_FONT_STEMS


def stroke_color_for(
    text: tuple[int, int, int],
    background: tuple[int, int, int],
) -> tuple[int, int, int]:
    light = (250, 250, 252)
    dark = (15, 17, 20)

    light_score = min(_contrast_ratio(light, text), _contrast_ratio(light, background))
    dark_score = min(_contrast_ratio(dark, text), _contrast_ratio(dark, background))
    return light if light_score >= dark_score else dark


def draw_text_stroke(
    draw: PIL.ImageDraw.ImageDraw,
    layout: TitleLayout,
    text: tuple[int, int, int],
    background: tuple[int, int, int],
) -> None:
    stroke_width = max(1, round(layout.font.size * 0.022))
    stroke_color = stroke_color_for(text, background)

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


class StrokeIsolation(IsolationTreatment):
    name = "stroke"
    rejects_self_contained_style = True

    def score(self, ctx: TextEffectContext) -> float:
        if ctx.font_size_ratio < 0.12:
            return 0.0

        if ctx.font_path.stem in CONDENSED_FONT_STEMS and ctx.font_size_ratio < 0.20:
            return 0.0

        score = 1.0

        if ctx.local_background_variance >= 0.18:
            score += 4.0
        elif ctx.local_background_variance >= 0.10:
            score += 2.0

        if ctx.minimum_text_contrast < 4.5:
            score += 2.0

        if ctx.local_background_variance < 0.04:
            score *= 0.25

        return max(0.0, score)

    def draw_foreground(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        draw_text_stroke(
            PIL.ImageDraw.Draw(state.image),
            ctx.layout,
            state.foreground_color,
            ctx.background,
        )
        state.foreground_drawn = True
