import PIL.Image
import PIL.ImageDraw

from ...common import _mix_rgb
from ..base import TextEffectContext, TextRenderContext, TextRenderState, TextStyle, TitleLayout
from ..font_groups import HEAVY_DISPLAY_FONT_STEMS


def draw_text_extrude(
    image: PIL.Image.Image,
    layout: TitleLayout,
    w: int,
    h: int,
    accent: tuple[int, int, int],
) -> PIL.Image.Image:
    steps = 4
    layer = PIL.Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer_draw = PIL.ImageDraw.Draw(layer)

    for depth in range(steps, 0, -1):
        shade = _mix_rgb(accent, (0, 0, 0), 0.12 * depth)
        layer_draw.multiline_text(
            (layout.text_x + depth, layout.text_y + depth),
            layout.rendered_text,
            font=layout.font,
            fill=(*shade, 255),
            spacing=layout.spacing,
            align=layout.align,
        )

    return PIL.Image.alpha_composite(image, layer)


class ExtrudeStyle(TextStyle):
    name = "extrude"

    def score(self, ctx: TextEffectContext, has_accent_word: bool) -> float:
        if ctx.font_path.stem not in HEAVY_DISPLAY_FONT_STEMS:
            return 0.0

        if ctx.font_size_ratio < 0.26:
            return 0.0

        if ctx.line_count > 1:
            return 0.0

        if ctx.local_background_variance > 0.08:
            return 0.0

        if ctx.accent_background_contrast < 4.0:
            return 0.0

        if ctx.text_width_ratio > 0.80:
            return 0.0

        return 1.0

    def prepare(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        state.image = draw_text_extrude(
            state.image,
            ctx.layout,
            ctx.w,
            ctx.h,
            ctx.accent,
        )
