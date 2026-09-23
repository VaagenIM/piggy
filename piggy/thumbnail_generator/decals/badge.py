"""Badge structural decal."""

import math
import random

import PIL.Image
import PIL.ImageDraw

from ..backgrounds import _CORNER_ZONES, _radial_color_layer
from ..common import _mix_rgb
from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect, _clear_side_zone, _decal_side, _point_in_box



class BadgeDecal(Decal):
    name = 'badge'
    pattern_conflicts = {}
    support_enabled = True

    def score(self, ctx: DecalContext) -> float:
        if ctx.line_count >= 3:
            return 0.0
        score = 2.0
        if ctx.layout == "left":
            score += 1.5
        if ctx.text_width_ratio > 0.78:
            score -= 2.0
        if ctx.background_complexity == 0:
            score += 1.0
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_badge(
            ctx.layer, ctx.w, ctx.h, ctx.accent, ctx.secondary, ctx.safe_bbox,
            ctx.layout, ctx.complexity, ctx.rng,
        )
        return DecalResult(layer, region)

    def draw_support(self, ctx: DecalRenderContext, x: float, y: float) -> None:
        draw = PIL.ImageDraw.Draw(ctx.layer)
        r = ctx.rng.uniform(3.0, 5.0)
        draw.polygon(
            [(x, y - r), (x + r, y), (x, y + r), (x - r, y)],
            outline=(*ctx.accent, 160),
        )


def _draw_decal_badge(
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
    An abstract geometric emblem -- 2-3 of {ring, hexagon, diamond,
    rounded square, crossing lines} combined into one motif, never a
    face/character/mascot.
    """
    side = _decal_side(layout, safe_bbox, w, decal_rng)
    zone = _clear_side_zone(side, safe_bbox, w, h, 0.32)

    if zone is None:
        return decal_layer, None

    zone_left, _, zone_right, _ = zone
    radius = min(zone_right - zone_left, h) * decal_rng.uniform(0.30, 0.40)

    if radius < 18:
        return decal_layer, None

    cx = (zone_left + zone_right) / 2
    cy = h * decal_rng.uniform(0.40, 0.60)
    box = (cx - radius, cy - radius, cx + radius, cy + radius)

    if _boxes_intersect(box, safe_bbox):
        cx = zone_right - radius - 6 if side == "right" else zone_left + radius + 6
        box = (cx - radius, cy - radius, cx + radius, cy + radius)

    decal_layer_before_glow = decal_layer

    if decal_rng.random() < 0.6:
        glow = _radial_color_layer((w, h), accent, cx, cy, radius * 1.6, 65)
        decal_layer = PIL.Image.alpha_composite(decal_layer_before_glow, glow)

    draw = PIL.ImageDraw.Draw(decal_layer)

    def _polygon_points(sides: int, r: float, rotation: float = 0.0) -> list[tuple[float, float]]:
        return [
            (
                cx + r * math.cos(rotation + math.tau * i / sides),
                cy + r * math.sin(rotation + math.tau * i / sides),
            )
            for i in range(sides)
        ]

    components = decal_rng.sample(
        ("ring", "hexagon", "diamond", "rounded_square", "crossing_lines"),
        k=decal_rng.choice((2, 3)),
    )

    for component in components:
        if component == "ring":
            draw.ellipse(box, outline=(*accent, 190), width=2)

        elif component == "hexagon":
            draw.polygon(_polygon_points(6, radius * 0.8, math.pi / 6), outline=(*accent, 170), width=2)

        elif component == "diamond":
            draw.polygon(
                _polygon_points(4, radius * 0.55, math.pi / 4),
                outline=(*_mix_rgb(accent, secondary, 0.4), 190),
                width=2,
            )

        elif component == "rounded_square":
            side_len = radius * 0.85
            draw.rounded_rectangle(
                (cx - side_len, cy - side_len, cx + side_len, cy + side_len),
                radius=side_len * 0.3,
                outline=(*accent, 150),
                width=2,
            )

        elif component == "crossing_lines":
            arm = radius * 0.9
            draw.line((cx - arm, cy, cx + arm, cy), fill=(*accent, 130), width=1)
            draw.line((cx, cy - arm, cx, cy + arm), fill=(*accent, 130), width=1)

    dot_r = max(2.5, radius * 0.08)
    draw.ellipse((cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r), fill=(*accent, 230))

    return decal_layer, box
