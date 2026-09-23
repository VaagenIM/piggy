"""Circuit Trace structural decal."""

import math
import random

import PIL.Image
import PIL.ImageDraw

from ..backgrounds import _CORNER_ZONES, _radial_color_layer
from ..common import _mix_rgb
from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect, _clear_side_zone, _decal_side, _point_in_box


class CircuitTraceDecal(Decal):
    name = "circuit_trace"
    pattern_conflicts = {"grid": 0.7}
    support_enabled = True

    def score(self, ctx: DecalContext) -> float:
        if ctx.line_count >= 3:
            return 0.5
        score = 2.8
        if ctx.layout == "left":
            score += 2.2
        if ctx.background_complexity == 0:
            score += 1.2
        elif ctx.background_complexity >= 2:
            score -= 1.0
        if ctx.text_width_ratio > 0.82:
            score -= 2.0
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_circuit_trace(
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
        r = ctx.rng.uniform(2.0, 3.2)
        draw.ellipse(
            (x - r, y - r, x + r, y + r),
            outline=(*ctx.accent, 140),
            width=1,
        )


def _draw_decal_circuit_trace(
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
    """Angular PCB-like traces with terminal dots."""

    side = _decal_side(layout, safe_bbox, w, decal_rng)
    zone = _clear_side_zone(side, safe_bbox, w, h, 0.40)

    if zone is None:
        return decal_layer, None

    left, _, right, _ = zone
    draw = PIL.ImageDraw.Draw(decal_layer)

    count = {0: 7, 1: 5, 2: 3}.get(complexity, 4)

    xs = []
    ys = []

    direction = -1 if side == "right" else 1

    for _ in range(count):
        x = decal_rng.uniform(left, right)
        y = decal_rng.uniform(h * 0.12, h * 0.88)

        horizontal_1 = decal_rng.uniform(w * 0.025, w * 0.075)
        vertical = decal_rng.uniform(h * 0.06, h * 0.22)
        horizontal_2 = decal_rng.uniform(w * 0.02, w * 0.06)

        vertical *= decal_rng.choice((-1, 1))

        points = [
            (x, y),
            (x + direction * horizontal_1, y),
            (x + direction * horizontal_1, y + vertical),
            (
                x + direction * (horizontal_1 + horizontal_2),
                y + vertical,
            ),
        ]

        if any(_point_in_box(px, py, safe_bbox) for px, py in points):
            continue

        line_color = _mix_rgb(accent, secondary, 0.25)

        draw.line(
            points,
            fill=(*line_color, decal_rng.randint(85, 145)),
            width=2,
            joint="curve",
        )

        # Terminal dots at both ends.
        for tx, ty in (points[0], points[-1]):
            r = decal_rng.uniform(2.5, 4.0)

            draw.ellipse(
                (tx - r, ty - r, tx + r, ty + r),
                fill=(*accent, 185),
            )

        xs.extend(px for px, _ in points)
        ys.extend(py for _, py in points)

    if not xs:
        return decal_layer, None

    return decal_layer, (
        round(min(xs) - 10),
        round(min(ys) - 10),
        round(max(xs) + 10),
        round(max(ys) + 10),
    )
