"""Blueprint Measure structural decal."""

import math
import random

import PIL.Image
import PIL.ImageDraw

from ..backgrounds import _CORNER_ZONES, _radial_color_layer
from ..common import _mix_rgb
from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect, _clear_side_zone, _decal_side, _point_in_box


class BlueprintMeasureDecal(Decal):
    name = "blueprint_measure"
    pattern_conflicts = {}
    support_enabled = True

    def score(self, ctx: DecalContext) -> float:
        score = 2.3
        if ctx.line_count >= 3:
            score *= 0.6
        if ctx.layout == "left":
            score += 1.4
        if ctx.background_complexity >= 2:
            score -= 0.5
        if ctx.text_width_ratio > 0.84:
            score -= 2.0
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_blueprint_measure(
            ctx.layer,
            ctx.w,
            ctx.h,
            ctx.accent,
            ctx.secondary,
            ctx.safe_bbox,
            ctx.layout,
            ctx.complexity,
            ctx.rng,
        )
        return DecalResult(layer, region)

    def draw_support(self, ctx: DecalRenderContext, x: float, y: float) -> None:
        draw = PIL.ImageDraw.Draw(ctx.layer)
        tick = ctx.rng.uniform(5, 10)
        draw.line((x - tick, y, x + tick, y), fill=(*ctx.accent, 90), width=1)
        draw.line(
            (x, y - tick * 0.6, x, y + tick * 0.6),
            fill=(*ctx.accent, 120),
            width=1,
        )


def _draw_decal_blueprint_measure(
    decal_layer: PIL.Image.Image,
    w: int,
    h: int,
    accent: tuple[int, int, int],
    secondary: tuple[int, int, int],
    safe_bbox: tuple[int, int, int, int],
    layout: str,
    complexity: int,
    decal_rng: random.Random,
) -> tuple[PIL.Image.Image, tuple[int, int, int, int] | None]:
    """Dimension lines and drafting-style measurement marks."""

    side = _decal_side(layout, safe_bbox, w, decal_rng)
    zone = _clear_side_zone(side, safe_bbox, w, h, 0.38)

    if zone is None:
        return decal_layer, None

    left, _, right, _ = zone
    draw = PIL.ImageDraw.Draw(decal_layer)

    x1 = decal_rng.uniform(left + 10, left + (right - left) * 0.30)
    x2 = decal_rng.uniform(
        left + (right - left) * 0.65,
        right - 10,
    )

    y = decal_rng.uniform(h * 0.28, h * 0.72)

    box = (
        x1 - 12,
        y - h * 0.14,
        x2 + 12,
        y + h * 0.14,
    )

    if _boxes_intersect(box, safe_bbox):
        return decal_layer, None

    color = _mix_rgb(accent, secondary, 0.2)

    # Main measurement line.
    draw.line(
        (x1, y, x2, y),
        fill=(*color, 125),
        width=1,
    )

    tick = h * 0.035

    # End caps.
    for x in (x1, x2):
        draw.line(
            (x, y - tick, x, y + tick),
            fill=(*accent, 175),
            width=2,
        )

    # Arrow-ish diagonal caps.
    arrow = max(5, h * 0.018)

    draw.line(
        (x1, y, x1 + arrow, y - arrow),
        fill=(*accent, 150),
        width=1,
    )

    draw.line(
        (x2, y, x2 - arrow, y + arrow),
        fill=(*accent, 150),
        width=1,
    )

    # Secondary parallel drafting line.
    if complexity <= 1:
        y2 = y + h * 0.075

        draw.line(
            (x1 + 10, y2, x2 - 10, y2),
            fill=(*secondary, 65),
            width=1,
        )

        # Small measurement ticks.
        for fraction in (0.25, 0.5, 0.75):
            x = x1 + (x2 - x1) * fraction

            draw.line(
                (
                    x,
                    y2 - tick * 0.45,
                    x,
                    y2 + tick * 0.45,
                ),
                fill=(*accent, 95),
                width=1,
            )

    return decal_layer, box
