"""Node Graph structural decal."""

import math
import random

import PIL.Image
import PIL.ImageDraw

from ..backgrounds import _CORNER_ZONES, _radial_color_layer
from ..common import _mix_rgb
from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect, _clear_side_zone, _decal_side, _point_in_box


class NodeGraphDecal(Decal):
    name = "node_graph"
    pattern_conflicts = {"dot_cluster": 0.55}
    support_enabled = True

    def score(self, ctx: DecalContext) -> float:
        if ctx.line_count >= 3:
            return 0.0
        score = 3.0
        if ctx.layout == "left":
            score += 3.0
        if ctx.background_complexity == 0:
            score += 1.5
        elif ctx.background_complexity == 2:
            score -= 1.0
        if ctx.text_width_ratio > 0.80:
            score -= 1.5
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_node_graph(
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
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(*ctx.accent, 130))


def _draw_decal_node_graph(
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
    An organic node/network motif -- a handful of nodes each linked to
    a couple of nearby neighbours (not a full mesh), one deliberate
    longer cross-connection, and one or two visually "stronger" focal
    nodes with a soft glow behind one of them.
    """
    side = _decal_side(layout, safe_bbox, w, decal_rng)
    zone = _clear_side_zone(side, safe_bbox, w, h, 0.40)

    if zone is None:
        return decal_layer, None

    zone_left, _, zone_right, _ = zone
    zone_top = round(h * 0.10)
    zone_bottom = round(h * 0.90)

    node_count = 9 if complexity == 0 else (7 if complexity == 1 else 5)

    nodes: list[tuple[float, float]] = []
    attempts = 0

    while len(nodes) < node_count and attempts < node_count * 6:
        attempts += 1
        x = decal_rng.uniform(zone_left, zone_right)
        y = decal_rng.uniform(zone_top, zone_bottom)

        if _point_in_box(x, y, safe_bbox):
            continue

        nodes.append((x, y))

    if len(nodes) < 3:
        return decal_layer, None

    draw = PIL.ImageDraw.Draw(decal_layer)

    # Connect each node to its 1-3 nearest neighbours rather than
    # every other node, so it reads as a deliberate graph.
    for i, (x1, y1) in enumerate(nodes):
        by_distance = sorted(
            range(len(nodes)),
            key=lambda j, x1=x1, y1=y1: (nodes[j][0] - x1) ** 2 + (nodes[j][1] - y1) ** 2,
        )
        neighbours = [j for j in by_distance if j != i][: decal_rng.choice((1, 2, 2, 3))]

        for j in neighbours:
            x2, y2 = nodes[j]
            draw.line(
                (x1, y1, x2, y2),
                fill=(*_mix_rgb(accent, secondary, 0.25), decal_rng.randint(50, 95)),
                width=1,
            )

    if len(nodes) >= 4:
        a, b = decal_rng.sample(range(len(nodes)), 2)
        draw.line((*nodes[a], *nodes[b]), fill=(*accent, 70), width=1)

    focal_indices = set(decal_rng.sample(range(len(nodes)), k=min(2, len(nodes))))

    for i, (x, y) in enumerate(nodes):
        if i in focal_indices:
            radius = decal_rng.uniform(4.5, 6.5)
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*accent, 210))
        else:
            radius = decal_rng.uniform(2.0, 3.2)
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=(*_mix_rgb(accent, secondary, 0.2), 150),
            )

    if focal_indices:
        gx, gy = nodes[next(iter(focal_indices))]
        glow = _radial_color_layer((w, h), accent, gx, gy, max(24, h * 0.16), 90)
        decal_layer = PIL.Image.alpha_composite(decal_layer, glow)

    xs = [x for x, _ in nodes]
    ys = [y for _, y in nodes]
    region = (
        round(min(xs) - 10),
        round(min(ys) - 10),
        round(max(xs) + 10),
        round(max(ys) + 10),
    )

    return decal_layer, region
