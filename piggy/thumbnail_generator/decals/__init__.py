"""Object-oriented structural decal system.

The renderer-facing underscore functions are kept as a compatibility facade,
while each decal owns its score, pattern conflicts, primary rendering, and
support rendering in one class/module.
"""

import random

import PIL.Image

from .base import DecalContext, DecalRenderContext
from .helpers import _expand_bbox, _point_in_box
from .registry import DECALS_BY_NAME, choose_primary_decal

# Backwards-compatible name currently imported by renderer.py.
_DecalContext = DecalContext


def _choose_primary_decal(ctx: DecalContext, decal_rng: random.Random) -> str:
    return choose_primary_decal(ctx, decal_rng).name


def _render_primary_decal(
    decal_layer: PIL.Image.Image,
    name: str,
    w: int,
    h: int,
    accent: tuple[int, int, int],
    secondary: tuple[int, int, int],
    safe_bbox: tuple[int, int, int, int],
    layout: str,
    complexity: int,
    decal_rng: random.Random,
) -> tuple[PIL.Image.Image, tuple[int, int, int, int] | None]:
    decal = DECALS_BY_NAME.get(name)
    if decal is None:
        return decal_layer, None

    ctx = DecalRenderContext(
        layer=decal_layer,
        w=w,
        h=h,
        accent=accent,
        secondary=secondary,
        safe_bbox=safe_bbox,
        layout=layout,
        complexity=complexity,
        rng=decal_rng,
    )
    result = decal.draw(ctx)
    return result.layer, result.region


def _render_supporting_decals(
    decal_layer: PIL.Image.Image,
    primary_name: str,
    region: tuple[int, int, int, int] | None,
    w: int,
    h: int,
    accent: tuple[int, int, int],
    safe_bbox: tuple[int, int, int, int],
    decal_rng: random.Random,
) -> PIL.Image.Image:
    decal = DECALS_BY_NAME.get(primary_name)
    if decal is None or not decal.support_enabled or region is None:
        return decal_layer

    # Preserve the original support-placement behaviour exactly.
    count = decal_rng.randint(0, 5)
    if count == 0:
        return decal_layer

    region_w = region[2] - region[0]
    region_h = region[3] - region[1]
    pad = max(20, round(max(region_w, region_h) * 0.25))

    # Supporting decals only need the active accent. The old function did not
    # receive secondary, so use accent for both fields to preserve its API.
    ctx = DecalRenderContext(
        layer=decal_layer,
        w=w,
        h=h,
        accent=accent,
        secondary=accent,
        safe_bbox=safe_bbox,
        layout="",
        complexity=0,
        rng=decal_rng,
    )

    placed = 0
    attempts = 0

    while placed < count and attempts < count * 6:
        attempts += 1

        x = min(max(decal_rng.uniform(region[0] - pad, region[2] + pad), 0), w)
        y = min(max(decal_rng.uniform(region[1] - pad, region[3] + pad), 0), h)

        if _point_in_box(x, y, safe_bbox):
            continue

        decal.draw_support(ctx, x, y)
        placed += 1

    return decal_layer


__all__ = [
    "DecalContext",
    "DecalRenderContext",
    "DECALS_BY_NAME",
    "choose_primary_decal",
    "_DecalContext",
    "_expand_bbox",
    "_choose_primary_decal",
    "_render_primary_decal",
    "_render_supporting_decals",
]
