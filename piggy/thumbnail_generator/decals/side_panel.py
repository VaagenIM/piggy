"""Side Panel structural decal."""

import math
import random

import PIL.Image
import PIL.ImageDraw

from ..backgrounds import _CORNER_ZONES, _radial_color_layer
from ..common import _mix_rgb
from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect, _clear_side_zone, _decal_side, _point_in_box


class SidePanelDecal(Decal):
    name = "side_panel"
    pattern_conflicts = {}
    support_enabled = True

    def score(self, ctx: DecalContext) -> float:
        if ctx.line_count >= 3:
            return 0.0
        score = 2.0
        if ctx.layout == "left":
            score += 2.5
        if ctx.text_width_ratio > 0.78:
            score -= 2.0
        if ctx.background_complexity >= 2:
            score -= 1.0
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_side_panel(
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
        length = ctx.rng.uniform(10, 26)
        angle = ctx.rng.uniform(0.3, 1.2)
        draw.line(
            (x, y, x + length * math.cos(angle), y + length * math.sin(angle)),
            fill=(*ctx.accent, 110),
            width=2,
        )


def _draw_decal_side_panel(
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
    """A broad, translucent angled panel occupying one side -- structure, not a button."""
    side = _decal_side(layout, safe_bbox, w, decal_rng)
    zone = _clear_side_zone(side, safe_bbox, w, h, 0.34)

    if zone is None or zone[2] - zone[0] < w * 0.12:
        return decal_layer, None

    zone_left, _, zone_right, _ = zone
    skew = decal_rng.uniform(0.06, 0.16) * w

    draw = PIL.ImageDraw.Draw(decal_layer)
    fill_color = secondary if decal_rng.random() < 0.5 else accent

    if side == "right":
        edge_top = (zone_left + skew, 0)
        edge_bottom = (zone_left - skew * 0.4, h)
        polygon = [edge_top, (w, 0), (w, h), edge_bottom]
    else:
        edge_top = (zone_right - skew, 0)
        edge_bottom = (zone_right + skew * 0.4, h)
        polygon = [(0, 0), edge_top, edge_bottom, (0, h)]

    draw.polygon(polygon, fill=(*fill_color, decal_rng.randint(45, 75)))
    draw.line((*edge_top, *edge_bottom), fill=(*accent, decal_rng.randint(110, 160)), width=2)

    # An occasional thinner second facet just inside the first, for layered depth.
    if decal_rng.random() < 0.5:
        offset = (zone_right - zone_left) * 0.3

        if side == "right":
            inner_top = (edge_top[0] + offset, 0)
            inner_bottom = (edge_bottom[0] + offset, h)

            if inner_top[0] < w:
                draw.polygon(
                    [inner_top, (w, 0), (w, h), inner_bottom],
                    fill=(*accent, decal_rng.randint(20, 40)),
                )
        else:
            inner_top = (edge_top[0] - offset, 0)
            inner_bottom = (edge_bottom[0] - offset, h)

            if inner_top[0] > 0:
                draw.polygon(
                    [(0, 0), inner_top, inner_bottom, (0, h)],
                    fill=(*accent, decal_rng.randint(20, 40)),
                )

    return decal_layer, zone
