import PIL.Image

from ..common import _hex_to_rgb
from .base import BackgroundContext, BackgroundStyle


class SolidBackground(BackgroundStyle):
    name = "solid"
    weight = 12
    complexity = 0

    def draw(self, ctx: BackgroundContext) -> PIL.Image.Image:
        color = _hex_to_rgb(ctx.palette.backgrounds[0])
        return PIL.Image.new("RGBA", ctx.size, (*color, 255))
