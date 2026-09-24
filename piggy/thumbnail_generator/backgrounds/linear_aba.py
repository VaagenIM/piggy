from ..common import _hex_to_rgb
from .base import BackgroundContext, BackgroundStyle
from .helpers import choose_linear_angle, linear_gradient_layer


class LinearABABackground(BackgroundStyle):
    name = "linear_aba"
    weight = 18
    complexity = 1

    def draw(self, ctx: BackgroundContext):
        a, b, _ = (_hex_to_rgb(color) for color in ctx.palette.backgrounds)
        angle = choose_linear_angle(ctx.rng)
        midpoint = ctx.rng.uniform(0.35, 0.65)
        return linear_gradient_layer(ctx.size, a, a, b, midpoint, angle)
