import PIL.Image
import PIL.ImageOps

from ..common import _hex_to_rgb
from .base import BackgroundContext, BackgroundStyle


class RadialBackground(BackgroundStyle):
    name = "radial"
    weight = 18
    complexity = 1

    def draw(self, ctx: BackgroundContext):
        color_a, _, color_b = (_hex_to_rgb(color) for color in ctx.palette.backgrounds)
        w, h = ctx.size

        center_x = ctx.rng.uniform(0.15, 0.85) * w
        center_y = ctx.rng.uniform(0.10, 0.90) * h

        corners = ((0, 0), (w, 0), (0, h), (w, h))
        max_dist = max(((center_x - x) ** 2 + (center_y - y) ** 2) ** 0.5 for x, y in corners)

        diameter = max(2, round(max_dist * 1.5))
        grad = PIL.Image.radial_gradient("L").resize((diameter, diameter))
        colored = PIL.ImageOps.colorize(grad, black=color_a, white=color_b).convert("RGBA")

        canvas = PIL.Image.new("RGBA", ctx.size, (*color_b, 255))
        canvas.paste(
            colored,
            (round(center_x - diameter / 2), round(center_y - diameter / 2)),
        )
        return canvas
