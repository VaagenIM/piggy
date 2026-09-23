"""Shared geometry and placement helpers for decals."""

import random

def _expand_bbox(
    bbox: tuple[int, int, int, int],
    padding_x: int,
    padding_y: int,
    w: int,
    h: int,
) -> tuple[int, int, int, int]:
    return (
        max(0, bbox[0] - padding_x),
        max(0, bbox[1] - padding_y),
        min(w, bbox[2] + padding_x),
        min(h, bbox[3] + padding_y),
    )


def _boxes_intersect(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def _point_in_box(x: float, y: float, box: tuple[float, float, float, float]) -> bool:
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def _decal_side(
    layout: str,
    safe_bbox: tuple[int, int, int, int],
    w: int,
    decal_rng: random.Random,
) -> str:
    """
    Which side a side-anchored decal (node graph / panel / badge)
    should occupy. Left-aligned text always pushes decals right;
    centred text picks whichever side the title actually leans away
    from, so this keeps working if a right-aligned layout is added
    later without decals needing to know about it explicitly.
    """
    if layout == "left":
        return "right"

    center_x = (safe_bbox[0] + safe_bbox[2]) / 2

    if center_x < w * 0.4:
        return "right"

    if center_x > w * 0.6:
        return "left"

    return decal_rng.choice(("left", "right"))


def _clear_side_zone(
    side: str,
    safe_bbox: tuple[int, int, int, int],
    w: int,
    h: int,
    width_fraction: float,
    gap: int = 14,
) -> tuple[int, int, int, int] | None:
    """
    A candidate rectangle on one side of the canvas, pushed clear of
    `safe_bbox` if the title would otherwise overlap it. Returns
    `None` when there genuinely isn't enough room left -- callers
    should skip the decal rather than draw into the title.
    """
    zone_w = round(w * width_fraction)

    if side == "right":
        left = w - zone_w

        if safe_bbox[2] > left:
            left = min(w - 60, safe_bbox[2] + gap)

        if left >= w - 40:
            return None

        return (left, 0, w, h)

    right = zone_w

    if safe_bbox[0] < right:
        right = max(60, safe_bbox[0] - gap)

    if right <= 40:
        return None

    return (0, 0, right, h)


