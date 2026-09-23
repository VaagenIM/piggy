"""Orbit Cluster structural decal."""

import math
import random

import PIL.Image
import PIL.ImageDraw

from ..backgrounds import _CORNER_ZONES, _radial_color_layer
from ..common import _mix_rgb
from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect


class OrbitClusterDecal(Decal):
    name = "orbit_cluster"
    pattern_conflicts = {"rings": 0.35}
    support_enabled = True

    def score(self, ctx: DecalContext) -> float:
        score = 0.5 if ctx.line_count >= 3 else 2.5
        if ctx.layout == "center":
            score += 2.0
        if ctx.background_style in ("solid", "linear_ab", "linear_aba", "radial"):
            score += 1.0
        if ctx.background_complexity >= 2:
            score -= 1.0
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_orbit_cluster(
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
        r = ctx.rng.uniform(2.0, 3.5)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(*ctx.accent, 150))


def _draw_decal_orbit_cluster(
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
    """
    A larger, more asymmetric relative of the ambient concentric-rings
    pattern: partial arcs, a ring or two, a couple of orbiting dots,
    and usually a soft focal glow -- anchored at a corner and often
    extending past the canvas edge rather than centred and self-
    contained.
    """
    candidates = [zone for zone in _CORNER_ZONES if not (layout == "left" and zone in ("top_left", "bottom_left"))]
    zone_name = decal_rng.choice(candidates)
    (x_lo, x_hi), (y_lo, y_hi) = _CORNER_ZONES[zone_name]

    cx = decal_rng.uniform(x_lo, x_hi) * w
    cy = decal_rng.uniform(y_lo, y_hi) * h
    base_radius = decal_rng.uniform(0.30, 0.48) * max(w, h)

    footprint = (cx - base_radius, cy - base_radius, cx + base_radius, cy + base_radius)

    if _boxes_intersect(footprint, safe_bbox):
        # Pull the whole cluster back toward its home corner instead
        # of drawing rings over the title.
        cx = x_lo * w if x_lo < 0.5 else x_hi * w
        cy = y_lo * h if y_lo < 0.5 else y_hi * h
        base_radius *= 0.7

    draw = PIL.ImageDraw.Draw(decal_layer)
    ring_count = 3 if complexity <= 1 else 2

    for i in range(ring_count):
        radius = base_radius * (0.45 + i * 0.28)
        box = (cx - radius, cy - radius, cx + radius, cy + radius)
        alpha = max(20, 75 - i * 16)

        if decal_rng.random() < 0.6:
            start = decal_rng.uniform(0, 360)
            extent = decal_rng.uniform(80, 220)
            draw.arc(box, start, start + extent, fill=(*accent, alpha), width=2)
        else:
            draw.ellipse(box, outline=(*_mix_rgb(accent, secondary, 0.3), alpha), width=1)

    dot_radius = base_radius * decal_rng.uniform(0.55, 0.85)

    for _ in range(decal_rng.randint(2, 4)):
        angle = math.radians(decal_rng.uniform(0, 360))
        dx = cx + dot_radius * math.cos(angle)
        dy = cy + dot_radius * math.sin(angle)

        if not (0 <= dx <= w and 0 <= dy <= h):
            continue

        r = decal_rng.uniform(2.5, 4.5)
        draw.ellipse((dx - r, dy - r, dx + r, dy + r), fill=(*accent, 180))

    if decal_rng.random() < 0.7:
        glow = _radial_color_layer((w, h), accent, cx, cy, base_radius * 0.5, 70)
        decal_layer = PIL.Image.alpha_composite(decal_layer, glow)

    region = (
        round(cx - base_radius),
        round(cy - base_radius),
        round(cx + base_radius),
        round(cy + base_radius),
    )

    return decal_layer, region
