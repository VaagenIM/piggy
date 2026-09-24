from ..common import _hex_to_rgb
from .base import BackgroundContext, BackgroundStyle
from .helpers import choose_linear_angle, linear_gradient_layer


class LinearABBackground(BackgroundStyle):
    name = "linear_ab"
    weight = 28
    complexity = 1

    def draw(self, ctx: BackgroundContext):
        a, _, c = (_hex_to_rgb(color) for color in ctx.palette.backgrounds)
        angle = choose_linear_angle(ctx.rng)
        return linear_gradient_layer(ctx.size, a, c, None, 0.5, angle)
