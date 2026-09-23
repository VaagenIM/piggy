import PIL.Image

from ..common import _hex_to_rgb
from .base import BackgroundContext, BackgroundStyle
from .helpers import CORNER_ZONES, OPPOSITE_CORNER, choose_glow_corner, radial_color_layer


class CornerGlowBackground(BackgroundStyle):
    name = "corner_glow"
    weight = 12
    complexity = 2

    def draw(self, ctx: BackgroundContext):
        base_color, bg1, bg2 = (_hex_to_rgb(color) for color in ctx.palette.backgrounds)
        bloom_colors = (bg2, bg1)
        w, h = ctx.size
        image = PIL.Image.new("RGBA", ctx.size, (*base_color, 255))

        zone = choose_glow_corner(ctx.layout, ctx.rng)
        zones = [zone]

        if ctx.rng.random() < 0.3:
            zones.append(OPPOSITE_CORNER[zone])

        for i, current_zone in enumerate(zones):
            (x_lo, x_hi), (y_lo, y_hi) = CORNER_ZONES[current_zone]
            center_x = ctx.rng.uniform(x_lo, x_hi) * w
            center_y = ctx.rng.uniform(y_lo, y_hi) * h
            radius = ctx.rng.uniform(0.55, 0.90) * max(w, h)
            color = bloom_colors[i % len(bloom_colors)]
            peak_alpha = 205 if i == 0 else 165

            glow = radial_color_layer(ctx.size, color, center_x, center_y, radius, peak_alpha)
            image = PIL.Image.alpha_composite(image, glow)

        return image
