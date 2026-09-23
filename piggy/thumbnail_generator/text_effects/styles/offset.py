import PIL.Image
import PIL.ImageDraw

from ..base import TextEffectContext, TextRenderContext, TextRenderState, TextStyle, TitleLayout
from ..font_groups import CONDENSED_FONT_STEMS, HEAVY_DISPLAY_FONT_STEMS


def draw_text_offset(
    image: PIL.Image.Image,
    layout: TitleLayout,
    w: int,
    h: int,
    accent: tuple[int, int, int],
    effect_rng,
) -> PIL.Image.Image:
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


class OffsetStyle(TextStyle):
    name = "offset"

    def score(self, ctx: TextEffectContext, has_accent_word: bool) -> float:
        if ctx.font_path.stem in CONDENSED_FONT_STEMS:
            return 0.0

        if ctx.font_size_ratio < 0.16:
            return 0.0

        if ctx.line_count >= 3:
            return 0.0

        score = 1.5

        if ctx.font_path.stem in HEAVY_DISPLAY_FONT_STEMS:
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
            score -= 1.5

        return max(0.0, score)

    def prepare(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        state.image = draw_text_offset(
            state.image,
            ctx.layout,
            ctx.w,
            ctx.h,
            ctx.accent,
            ctx.rng,
        )
