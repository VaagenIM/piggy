import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter

from ..base import TextEffectContext, TextRenderContext, TextRenderState, TextStyle, TitleLayout
from ..font_groups import TECH_FONT_STEMS


def draw_text_glow(
    image: PIL.Image.Image,
    layout: TitleLayout,
    w: int,
    h: int,
    glow_color: tuple[int, int, int],
    opacity: int = 80,
) -> PIL.Image.Image:
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


class GlowStyle(TextStyle):
    name = "glow"

    def score(self, ctx: TextEffectContext, has_accent_word: bool) -> float:
        if ctx.local_background_luminance >= 0.45:
            return 0.0

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

        if ctx.font_path.stem in TECH_FONT_STEMS:
            score += 1.5

        if ctx.line_count == 1:
            score += 1.0

        if ctx.font_size_ratio >= 0.24:
            score += 1.0

        return max(0.0, score)

    def prepare(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        state.image = draw_text_glow(
            state.image,
            ctx.layout,
            ctx.w,
            ctx.h,
            ctx.accent,
        )
