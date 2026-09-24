import PIL.Image
import PIL.ImageDraw

from ...common import _ensure_text_contrast
from ..base import IsolationTreatment, TextEffectContext, TextRenderContext, TextRenderState


def draw_highlight_block(
    image: PIL.Image.Image,
    w: int,
    h: int,
    text_bbox: tuple[int, int, int, int],
    text: tuple[int, int, int],
    accent: tuple[int, int, int],
    background: tuple[int, int, int],
) -> tuple[PIL.Image.Image, tuple[int, int, int]]:
    pad_x = max(20, round(w * 0.028))
    pad_y = max(16, round(h * 0.05))

    box = (
        max(0, text_bbox[0] - pad_x),
        max(0, text_bbox[1] - pad_y),
        min(w, text_bbox[2] + pad_x),
        min(h, text_bbox[3] + pad_y),
    )

    layer = PIL.Image.new("RGBA", (w, h), (0, 0, 0, 0))
    PIL.ImageDraw.Draw(layer).rounded_rectangle(
        box,
        radius=max(10, h // 18),
        fill=(*accent, 235),
    )

    safe_text = _ensure_text_contrast(text, accent, minimum=4.5)
    return PIL.Image.alpha_composite(image, layer), safe_text


class HighlightIsolation(IsolationTreatment):
    name = "highlight"
    suppresses_style = True

    def score(self, ctx: TextEffectContext) -> float:
        score = 0.0

        if ctx.minimum_text_contrast < 3.5:
            score += 5.0

        if ctx.local_background_variance >= 0.28:
            score += 4.0

        if ctx.pattern_density >= 0.35:
            score += 2.0

        if ctx.line_count >= 3 and ctx.local_background_variance >= 0.15:
            score += 1.5

        return score

    def prepare(self, ctx: TextRenderContext, state: TextRenderState) -> None:
        state.image, state.foreground_color = draw_highlight_block(
            state.image,
            ctx.w,
            ctx.h,
            ctx.layout.text_bbox,
            state.foreground_color,
            ctx.accent,
            ctx.background,
        )
