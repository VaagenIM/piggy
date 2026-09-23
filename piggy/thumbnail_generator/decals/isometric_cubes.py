"""Isometric Cubes structural decal."""

import math
import random

import PIL.Image
import PIL.ImageDraw

from ..backgrounds import _CORNER_ZONES, _radial_color_layer
from ..common import _mix_rgb
from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect, _clear_side_zone, _decal_side, _point_in_box



class IsometricCubesDecal(Decal):
    name = 'isometric_cubes'
    pattern_conflicts = {}
    support_enabled = True

    def score(self, ctx: DecalContext) -> float:
        if ctx.line_count >= 3:
            return 0.0
        score = 2.3
        if ctx.layout == "left":
            score += 1.5
        if ctx.background_complexity == 0:
            score += 1.5
        if ctx.background_complexity >= 2:
            score -= 1.0
        if ctx.text_width_ratio > 0.78:
            score -= 2.0
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_isometric_cubes(
            ctx.layer, ctx.w, ctx.h, ctx.accent, ctx.secondary, ctx.safe_bbox,
            ctx.layout, ctx.complexity, ctx.rng,
        )
        return DecalResult(layer, region)

    def draw_support(self, ctx: DecalRenderContext, x: float, y: float) -> None:
        draw = PIL.ImageDraw.Draw(ctx.layer)
        r = ctx.rng.uniform(3.0, 5.0)
        draw.polygon(
            [(x, y - r), (x + r, y), (x, y + r), (x - r, y)],
            outline=(*ctx.accent, 110),
            width=1,
        )


def _draw_decal_isometric_cubes(
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
    """Sparse isometric wireframe cubes."""

    side = _decal_side(layout, safe_bbox, w, decal_rng)
    zone = _clear_side_zone(side, safe_bbox, w, h, 0.38)

    if zone is None:
        return decal_layer, None

    left, _, right, _ = zone
    draw = PIL.ImageDraw.Draw(decal_layer)

    cube_count = {
        0: 3,
        1: 2,
        2: 1,
    }.get(complexity, 2)

    regions = []

    for _ in range(cube_count):
        size = decal_rng.uniform(h * 0.10, h * 0.19)

        cx = decal_rng.uniform(
            left + size,
            max(left + size + 1, right - size),
        )

        cy = decal_rng.uniform(
            h * 0.18,
            h * 0.82,
        )

        dx = size
        dy = size * 0.5
        height = size

        top = [
            (cx, cy - dy),
            (cx + dx, cy),
            (cx, cy + dy),
            (cx - dx, cy),
        ]

        bottom = [
            (x, y + height)
            for x, y in top
        ]

        box = (
            cx - dx,
            cy - dy,
            cx + dx,
            cy + dy + height,
        )

        if _boxes_intersect(box, safe_bbox):
            continue

        color = _mix_rgb(
            accent,
            secondary,
            decal_rng.uniform(0.1, 0.4),
        )

        alpha = decal_rng.randint(90, 150)

        # Top diamond.
        draw.line(
            top + [top[0]],
            fill=(*color, alpha),
            width=2,
        )

        # Bottom diamond.
        draw.line(
            bottom + [bottom[0]],
            fill=(*color, max(50, alpha - 35)),
            width=1,
        )

        # Vertical edges.
        for a, b in zip(top, bottom):
            draw.line(
                (*a, *b),
                fill=(*accent, alpha),
                width=2,
            )

        regions.append(box)

    if not regions:
        return decal_layer, None

    return decal_layer, (
        round(min(box[0] for box in regions)),
        round(min(box[1] for box in regions)),
        round(max(box[2] for box in regions)),
        round(max(box[3] for box in regions)),
    )
