import PIL.Image
import PIL.ImageDraw

from ...common import _mix_rgb
from ..base import TextEffectContext, TextRenderContext, TextRenderState, TextStyle, TitleLayout
from ..font_groups import CONDENSED_FONT_STEMS
from ..helpers import linear_text_fill


def draw_gradient_text(
    image: PIL.Image.Image,
    layout: TitleLayout,
    w: int,
    h: int,
    text: tuple[int, int, int],
    accent: tuple[int, int, int],
    effect_rng,
) -> PIL.Image.Image:
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

    fill = linear_text_fill(w, h, text, end_color, angle)
    fill.putalpha(mask)
    return PIL.Image.alpha_composite(image, fill)


class GradientStyle(TextStyle):
    name = "gradient"
    self_contained = True

    def score(self, ctx: TextEffectContext, has_accent_word: bool) -> float:
        if ctx.font_size_ratio < 0.18:
            return 0.0

        if ctx.line_count >= 3:
            return 0.0

        if ctx.font_path.stem in CONDENSED_FONT_STEMS:
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

    def draw_foreground(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        state.image = draw_gradient_text(
            state.image,
            ctx.layout,
            ctx.w,
            ctx.h,
            state.foreground_color,
            ctx.accent,
            ctx.rng,
        )
        state.foreground_drawn = True
