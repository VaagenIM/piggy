"""Shared rendering helpers for background styles."""

import math

import PIL.Image
import PIL.ImageOps

from ..common import _weighted_choice


LINEAR_ANGLE_WEIGHTS = {
    90: 26,
    -90: 22,
    45: 14,
    -45: 12,
    135: 10,
    -135: 8,
    0: 5,
    180: 3,
}

PATTERN_STRENGTH_BY_COMPLEXITY = {0: 1.0, 1: 0.85, 2: 0.6}

CORNER_ZONES = {
    "top_left": ((-0.15, 0.30), (-0.15, 0.30)),
    "top_right": ((0.70, 1.15), (-0.15, 0.30)),
    "bottom_left": ((-0.15, 0.30), (0.70, 1.15)),
    "bottom_right": ((0.70, 1.15), (0.70, 1.15)),
}

OPPOSITE_CORNER = {
    "top_left": "bottom_right",
    "top_right": "bottom_left",
    "bottom_left": "top_right",
    "bottom_right": "top_left",
}


def scale_layer_alpha(layer: PIL.Image.Image, factor: float) -> PIL.Image.Image:
    if factor >= 0.999:
        return layer

    r, g, b, a = layer.split()
    a = a.point(lambda value: round(value * factor))
    return PIL.Image.merge("RGBA", (r, g, b, a))


def linear_gradient_layer(
    size: tuple[int, int],
    black: tuple[int, int, int],
    white: tuple[int, int, int],
    mid: tuple[int, int, int] | None,
    midpoint_fraction: float,
    angle: int,
) -> PIL.Image.Image:
    w, h = size
    theta = math.radians(angle)

    span_h = max(2, round(w * abs(math.sin(theta)) + h * abs(math.cos(theta))) + 4)
    span_w = max(2, round(w * abs(math.cos(theta)) + h * abs(math.sin(theta))) + 4)

    grad = PIL.Image.linear_gradient("L").resize((span_w, span_h))

    if angle:
        grad = grad.rotate(angle, resample=PIL.Image.BICUBIC, expand=True)

    left = (grad.width - w) // 2
    top = (grad.height - h) // 2
    grad = grad.crop((left, top, left + w, top + h))

    colored = PIL.ImageOps.colorize(
        grad,
        black=black,
        white=white,
        mid=mid,
        midpoint=round(midpoint_fraction * 255),
    )
    return colored.convert("RGBA")


def choose_linear_angle(rng) -> int:
    return _weighted_choice(LINEAR_ANGLE_WEIGHTS, rng)


def radial_color_layer(
    size: tuple[int, int],
    color: tuple[int, int, int],
    center_x: float,
    center_y: float,
    radius: float,
    peak_alpha: int,
) -> PIL.Image.Image:
    diameter = max(2, round(radius * 2))
    grad = PIL.Image.radial_gradient("L").resize((diameter, diameter))
    alpha = PIL.ImageOps.invert(grad).point(lambda value: round(value * peak_alpha / 255))

    patch = PIL.Image.new("RGBA", (diameter, diameter), (*color, 0))
    patch.putalpha(alpha)

    layer = PIL.Image.new("RGBA", size, (0, 0, 0, 0))
    layer.paste(
        patch,
        (round(center_x - diameter / 2), round(center_y - diameter / 2)),
        patch,
    )
    return layer


def choose_glow_corner(layout: str, rng) -> str:
    if layout == "left":
        return rng.choice(("top_right", "bottom_right"))
    return rng.choice(tuple(CORNER_ZONES))
