"""Generic title-effect rendering pipeline."""

import PIL.Image
import PIL.ImageDraw

from .base import IsolationTreatment, TextRenderContext, TextRenderState, TextStyle
from .helpers import draw_text_plain


def render_title(
    image: PIL.Image.Image,
    isolation: IsolationTreatment,
    style: TextStyle,
    ctx: TextRenderContext,
) -> PIL.Image.Image:
    """Render one reconciled isolation + style combination."""
    state = TextRenderState(
        image=image,
        foreground_color=ctx.text,
    )

    # Preserve the old ordering exactly:
    # highlight/shadow first, then glow/offset/extrude, then the final glyph draw.
    isolation.prepare(ctx, state)
    style.prepare(ctx, state)

    isolation.draw_foreground(ctx, state)
    if not state.foreground_drawn:
        style.draw_foreground(ctx, state)

    if not state.foreground_drawn:
        draw_text_plain(
            PIL.ImageDraw.Draw(state.image),
            ctx.layout,
            state.foreground_color,
            ctx.background,
        )

    return state.image
