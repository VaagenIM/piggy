"""Shared low-level text rendering helpers."""

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

from ..common import _mix_rgb
from .base import TitleLayout


def line_positions(
    draw: PIL.ImageDraw.ImageDraw,
    lines: list[str],
    font: PIL.ImageFont.FreeTypeFont,
    spacing: int,
    align: str,
    x: float,
    y: float,
) -> list[tuple[float, float]]:
    line_height = draw.textbbox((0, 0), "A", font=font)[3] + spacing
    widths = [draw.textlength(line, font=font) for line in lines]
    max_width = max(widths, default=0)

    positions = []
    top = y
    for line, width in zip(lines, widths):
        left = x + (max_width - width) / 2 if align == "center" else x
        positions.append((left, top))
        top += line_height
    return positions


def draw_text_plain(
    draw: PIL.ImageDraw.ImageDraw,
    layout: TitleLayout,
    text: tuple[int, int, int],
    background: tuple[int, int, int],
) -> None:
    stroke_width = max(1, layout.font.size // 48)
    draw.multiline_text(
        (layout.text_x, layout.text_y),
        layout.rendered_text,
        font=layout.font,
        fill=(*text, 255),
        spacing=layout.spacing,
        align=layout.align,
        stroke_width=stroke_width,
        stroke_fill=(*background, 225),
    )


def linear_text_fill(
    w: int,
    h: int,
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
    angle: float,
) -> PIL.Image.Image:
    pad = round(max(w, h) * 0.4)
    grad_w = w + pad * 2
    grad_h = h + pad * 2

    gradient = PIL.Image.new("RGBA", (grad_w, grad_h), (0, 0, 0, 0))
    gradient_draw = PIL.ImageDraw.Draw(gradient)

    for y in range(grad_h):
        amount = y / max(1, grad_h - 1)
        gradient_draw.line(
            (0, y, grad_w, y),
            fill=(*_mix_rgb(top_color, bottom_color, amount), 255),
        )

    if angle:
        gradient = gradient.rotate(angle, resample=PIL.Image.BICUBIC)

    left = (gradient.width - w) // 2
    top = (gradient.height - h) // 2
    return gradient.crop((left, top, left + w, top + h))
