"""Ribbon structural decal."""

import math
import random

import PIL.Image
import PIL.ImageDraw

from ..backgrounds import _CORNER_ZONES, _radial_color_layer
from ..common import _mix_rgb
from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect, _clear_side_zone, _decal_side, _point_in_box



class RibbonDecal(Decal):
    name = 'ribbon'
    pattern_conflicts = {'diagonal_blocks': 0.3}
    support_enabled = True

    def score(self, ctx: DecalContext) -> float:
        if ctx.line_count >= 3:
            return 0.0
        score = 2.0
        if ctx.background_complexity == 0:
            score += 2.0
        elif ctx.background_complexity == 2:
            score -= 1.5
        if ctx.text_width_ratio > 0.82:
            score -= 1.5
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_ribbon(
            ctx.layer, ctx.w, ctx.h, ctx.accent, ctx.secondary, ctx.safe_bbox,
            ctx.layout, ctx.complexity, ctx.rng,
        )
        return DecalResult(layer, region)

    def draw_support(self, ctx: DecalRenderContext, x: float, y: float) -> None:
        draw = PIL.ImageDraw.Draw(ctx.layer)
        length = ctx.rng.uniform(10, 24)
        draw.line((x, y, x + length, y - length * 0.4), fill=(*ctx.accent, 100), width=2)


def _draw_decal_ribbon(
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
    """One deliberate large diagonal band across an outer region -- a bigger gesture than the ambient diagonal-blocks pattern."""
    side = "right" if layout == "left" else decal_rng.choice(("left", "right"))

    band_w = round(w * decal_rng.uniform(0.16, 0.26))
    skew = round(h * decal_rng.uniform(0.6, 1.1))
    direction = 1 if side == "right" else -1

    x = round(w * decal_rng.uniform(0.78, 0.92)) if side == "right" else round(w * decal_rng.uniform(0.06, 0.20))

    polygon = [
        (x, -skew * 0.2),
        (x + band_w, -skew * 0.2),
        (x + band_w + direction * skew, h + skew * 0.2),
        (x + direction * skew, h + skew * 0.2),
    ]

    box = (min(p[0] for p in polygon), 0, max(p[0] for p in polygon), h)

    if _boxes_intersect(box, safe_bbox):
        return decal_layer, None

    draw = PIL.ImageDraw.Draw(decal_layer)
    color = secondary if decal_rng.random() < 0.5 else accent
    draw.polygon(polygon, fill=(*color, decal_rng.randint(45, 80)))

    if decal_rng.random() < 0.4:
        offset = round(band_w * 0.7)
        draw.polygon([(px + offset, py) for px, py in polygon], fill=(*accent, decal_rng.randint(25, 45)))

    return decal_layer, box
