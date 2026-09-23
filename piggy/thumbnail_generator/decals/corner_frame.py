"""Corner Frame structural decal."""

import random

import PIL.Image
import PIL.ImageDraw

from .base import Decal, DecalContext, DecalRenderContext, DecalResult
from .helpers import _boxes_intersect


class CornerFrameDecal(Decal):
    name = "corner_frame"
    pattern_conflicts = {"corner_geometry": 0.4}
    support_enabled = False

    def score(self, ctx: DecalContext) -> float:
        score = 3.0
        if ctx.line_count >= 3:
            score += 3.0
        if ctx.background_complexity >= 2:
            score += 1.5
        return max(0.0, score)

    def draw(self, ctx: DecalRenderContext) -> DecalResult:
        layer, region = _draw_decal_corner_frame(
            ctx.layer,
            ctx.w,
            ctx.h,
            ctx.accent,
            ctx.safe_bbox,
            ctx.layout,
            ctx.complexity,
            ctx.rng,
        )
        return DecalResult(layer, region)


def _draw_decal_corner_frame(
    decal_layer: PIL.Image.Image,
    w: int,
    h: int,
    accent: tuple[int, int, int],
    safe_bbox: tuple[int, int, int, int],
    layout: str,
    complexity: int,
    decal_rng: random.Random,
) -> tuple[PIL.Image.Image, tuple[int, int, int, int] | None]:
    """Restrained corner brackets -- the safest, most minimal decal; works well over an already-busy background."""
    candidates = (
        ["top_right", "bottom_right"]
        if layout == "left"
        else [
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
        ]
    )

    corner_count = 1 if decal_rng.random() < 0.55 else 2
    corners = decal_rng.sample(candidates, k=min(corner_count, len(candidates)))

    draw = PIL.ImageDraw.Draw(decal_layer)
    arm = round(min(w, h) * decal_rng.uniform(0.10, 0.16))
    margin = round(min(w, h) * 0.05)
    region = None

    for corner in corners:
        if corner == "top_left":
            x, y, sx, sy = margin, margin, 1, 1
        elif corner == "top_right":
            x, y, sx, sy = w - margin, margin, -1, 1
        elif corner == "bottom_left":
            x, y, sx, sy = margin, h - margin, 1, -1
        else:
            x, y, sx, sy = w - margin, h - margin, -1, -1

        box = (
            min(x, x + sx * arm),
            min(y, y + sy * arm),
            max(x, x + sx * arm),
            max(y, y + sy * arm),
        )

        if _boxes_intersect(box, safe_bbox):
            continue

        draw.line((x, y, x + sx * arm, y), fill=(*accent, 150), width=2)
        draw.line((x, y, x, y + sy * arm), fill=(*accent, 150), width=2)

        dot_r = 2.5
        draw.ellipse(
            (x + sx * arm - dot_r, y - dot_r, x + sx * arm + dot_r, y + dot_r),
            fill=(*accent, 190),
        )

        if decal_rng.random() < 0.5:
            offset = round(arm * 0.35)
            tick_y = y + sy * (arm * 0.6)
            draw.line(
                (x + sx * offset, tick_y, x + sx * arm, tick_y),
                fill=(*accent, 90),
                width=1,
            )

        region = (
            box
            if region is None
            else (
                min(region[0], box[0]),
                min(region[1], box[1]),
                max(region[2], box[2]),
                max(region[3], box[3]),
            )
        )

    return decal_layer, region
