from ..common import _hex_to_rgb
from .base import BackgroundContext, BackgroundStyle
from .helpers import choose_linear_angle, linear_gradient_layer


class LinearABCBackground(BackgroundStyle):
    name = "linear_abc"
    weight = 12
    complexity = 2

    def draw(self, ctx: BackgroundContext):
        a, b, c = (_hex_to_rgb(color) for color in ctx.palette.backgrounds)
        angle = choose_linear_angle(ctx.rng)
        midpoint = ctx.rng.uniform(0.40, 0.60)
        return linear_gradient_layer(ctx.size, a, c, b, midpoint, angle)
