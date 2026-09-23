"""Hex Cluster structural decal."""

import math
import random

import PIL.Image
import PIL.ImageDraw

from ..backgrounds import _CORNER_ZONES, _radial_color_layer
from ..common import _mix_rgb
from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect, _clear_side_zone, _decal_side, _point_in_box



class HexClusterDecal(Decal):
    name = 'hex_cluster'
    pattern_conflicts = {}
    support_enabled = True

    def score(self, ctx: DecalContext) -> float:
        if ctx.line_count >= 3:
            return 0.5
        score = 2.5
        if ctx.layout == "left":
            score += 1.5
        if ctx.background_complexity == 0:
            score += 1.0
        elif ctx.background_complexity >= 2:
            score -= 0.8
        if ctx.text_width_ratio > 0.80:
            score -= 1.5
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_hex_cluster(
            ctx.layer, ctx.w, ctx.h, ctx.accent, ctx.secondary, ctx.safe_bbox,
            ctx.layout, ctx.complexity, ctx.rng,
        )
        return DecalResult(layer, region)

    def draw_support(self, ctx: DecalRenderContext, x: float, y: float) -> None:
        draw = PIL.ImageDraw.Draw(ctx.layer)
        r = ctx.rng.uniform(3.0, 5.0)
        points = [
            (
                x + math.cos(math.tau * i / 6) * r,
                y + math.sin(math.tau * i / 6) * r,
            )
            for i in range(6)
        ]
        draw.polygon(points, outline=(*ctx.accent, 120), width=1)


def _draw_decal_hex_cluster(
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
    """A compact cluster of connected hexagonal cells."""

    side = _decal_side(layout, safe_bbox, w, decal_rng)
    zone = _clear_side_zone(side, safe_bbox, w, h, 0.36)

    if zone is None:
        return decal_layer, None

    left, _, right, _ = zone

    radius = decal_rng.uniform(h * 0.045, h * 0.075)

    cx = (left + right) / 2
    cy = decal_rng.uniform(h * 0.35, h * 0.65)

    offsets = [
        (0, 0),
        (radius * 1.55, radius * 0.9),
        (radius * 1.55, -radius * 0.9),
        (-radius * 1.55, radius * 0.9),
        (-radius * 1.55, -radius * 0.9),
        (0, radius * 1.8),
        (0, -radius * 1.8),
    ]

    count = {
        0: decal_rng.randint(5, 7),
        1: decal_rng.randint(4, 6),
        2: decal_rng.randint(3, 4),
    }.get(complexity, 4)

    chosen = decal_rng.sample(
        offsets,
        k=min(count, len(offsets)),
    )

    def hex_points(
        x: float,
        y: float,
        r: float,
    ) -> list[tuple[float, float]]:
        return [
            (
                x + math.cos(math.tau * i / 6) * r,
                y + math.sin(math.tau * i / 6) * r,
            )
            for i in range(6)
        ]

    boxes = []

    for ox, oy in chosen:
        x = cx + ox
        y = cy + oy

        box = (
            x - radius,
            y - radius,
            x + radius,
            y + radius,
        )

        if _boxes_intersect(box, safe_bbox):
            continue

        boxes.append((x, y, box))

    if not boxes:
        return decal_layer, None

    draw = PIL.ImageDraw.Draw(decal_layer)

    for index, (x, y, box) in enumerate(boxes):
        color = (
            accent
            if index == 0
            else _mix_rgb(accent, secondary, 0.35)
        )

        alpha = 175 if index == 0 else 105

        draw.polygon(
            hex_points(x, y, radius),
            outline=(*color, alpha),
            width=2 if index == 0 else 1,
        )

        if index == 0:
            dot = max(2, radius * 0.10)

            draw.ellipse(
                (
                    x - dot,
                    y - dot,
                    x + dot,
                    y + dot,
                ),
                fill=(*accent, 210),
            )

    return decal_layer, (
        round(min(box[0] for _, _, box in boxes)),
        round(min(box[1] for _, _, box in boxes)),
        round(max(box[2] for _, _, box in boxes)),
        round(max(box[3] for _, _, box in boxes)),
    )
