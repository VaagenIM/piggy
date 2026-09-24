import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter

from ..base import IsolationTreatment, TextEffectContext, TextRenderContext, TextRenderState, TitleLayout


SHADOW_COLOR = (8, 9, 12)


def draw_text_shadow(
    image: PIL.Image.Image,
    layout: TitleLayout,
    w: int,
    h: int,
    color: tuple[int, int, int] = SHADOW_COLOR,
    opacity: int = 95,
) -> PIL.Image.Image:
    font_size = layout.font.size
    dx = max(1, round(font_size * 0.035))
    dy = max(2, round(font_size * 0.05))
    blur = max(1.0, font_size * 0.03)

    shadow = PIL.Image.new("RGBA", (w, h), (0, 0, 0, 0))
    PIL.ImageDraw.Draw(shadow).multiline_text(
        (layout.text_x + dx, layout.text_y + dy),
        layout.rendered_text,
        font=layout.font,
        fill=(*color, opacity),
        spacing=layout.spacing,
        align=layout.align,
    )
    shadow = shadow.filter(PIL.ImageFilter.GaussianBlur(blur))
    return PIL.Image.alpha_composite(image, shadow)


class ShadowIsolation(IsolationTreatment):
    name = "shadow"

    def score(self, ctx: TextEffectContext) -> float:
        if ctx.font_size_ratio < 0.10:
            return 0.0

        score = 2.0

        if 0.03 <= ctx.local_background_variance <= 0.22:
            score += 3.0
        elif ctx.local_background_variance > 0.22:
            score += 1.0

        if 3.5 <= ctx.minimum_text_contrast <= 7.0:
            score += 2.0

        score += ctx.pattern_density * 3.0

        if ctx.font_size_ratio >= 0.18:
            score += 1.0

        if ctx.minimum_text_contrast >= 8.0 and ctx.local_background_variance < 0.03:
            score *= 0.3

        return max(0.0, score)

    def prepare(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        state.image = draw_text_shadow(state.image, ctx.layout, ctx.w, ctx.h)
