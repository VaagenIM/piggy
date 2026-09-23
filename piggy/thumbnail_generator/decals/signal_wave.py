"""Signal Wave structural decal."""

import math
import random

import PIL.Image
import PIL.ImageDraw

from ..backgrounds import _CORNER_ZONES, _radial_color_layer
from ..common import _mix_rgb
from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect, _clear_side_zone, _decal_side, _point_in_box


class SignalWaveDecal(Decal):
    name = "signal_wave"
    pattern_conflicts = {"waves": 0.25}
    support_enabled = True

    def score(self, ctx: DecalContext) -> float:
        if ctx.line_count >= 3:
            return 0.0
        score = 2.2
        if ctx.layout == "left":
            score += 1.8
        if ctx.background_complexity <= 1:
            score += 1.0
        if ctx.text_width_ratio > 0.80:
            score -= 2.0
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_signal_wave(
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
        length = ctx.rng.uniform(10, 22)
        draw.line((x, y, x + length, y), fill=(*ctx.accent, 90), width=1)
        r = 2
        draw.ellipse(
            (x + length - r, y - r, x + length + r, y + r),
            fill=(*ctx.accent, 130),
        )


def _draw_decal_signal_wave(
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
    """A contained signal / oscilloscope-style waveform."""

    side = _decal_side(layout, safe_bbox, w, decal_rng)
    zone = _clear_side_zone(side, safe_bbox, w, h, 0.40)

    if zone is None:
        return decal_layer, None

    left, _, right, _ = zone

    margin = max(12, round(w * 0.012))
    x1 = left + margin
    x2 = right - margin

    if x2 - x1 < w * 0.12:
        return decal_layer, None

    cy = decal_rng.uniform(h * 0.35, h * 0.65)
    amplitude = decal_rng.uniform(h * 0.06, h * 0.15)

    box = (
        x1,
        cy - amplitude * 1.5,
        x2,
        cy + amplitude * 1.5,
    )

    if _boxes_intersect(box, safe_bbox):
        return decal_layer, None

    draw = PIL.ImageDraw.Draw(decal_layer)

    points = []

    steps = 36

    phase = decal_rng.uniform(0, math.tau)
    frequency = decal_rng.uniform(1.5, 3.2)

    for i in range(steps + 1):
        t = i / steps
        x = x1 + (x2 - x1) * t

        # Combining two waves makes it look less like a textbook sine wave.
        y = (
            cy
            + math.sin(t * math.tau * frequency + phase) * amplitude
            + math.sin(t * math.tau * frequency * 2.7 + phase) * amplitude * 0.22
        )

        points.append((x, y))

    draw.line(
        points,
        fill=(*accent, 165),
        width=2,
    )

    # Faint baseline.
    draw.line(
        (x1, cy, x2, cy),
        fill=(*secondary, 55),
        width=1,
    )

    # Sample points.
    for i in range(4, steps, 8):
        x, y = points[i]
        r = 2.5

        draw.ellipse(
            (x - r, y - r, x + r, y + r),
            fill=(*accent, 205),
        )

    return decal_layer, box
