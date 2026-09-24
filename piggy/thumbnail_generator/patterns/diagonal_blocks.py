"""Broad translucent diagonal-block ambient pattern."""

from .base import Pattern, PatternContext


class DiagonalBlocksPattern(Pattern):
    name = "diagonal_blocks"

    def draw(self, ctx: PatternContext) -> None:
        direction = ctx.rng.choice((-1, 1))

        band_w = ctx.rng.randint(
            max(70, ctx.w // 10),
            max(110, ctx.w // 6),
        )

        x = ctx.rng.choice(
            (
                int(ctx.w * 0.78),
                int(ctx.w * 0.08),
            )
        )

        for i in range(3):
            offset = i * int(band_w * 0.55)
            alpha = 45 - i * 8

            if direction > 0:
                points = [
                    (x + offset, -ctx.h * 0.15),
                    (x + band_w + offset, -ctx.h * 0.15),
                    (x + offset, ctx.h * 1.15),
                    (x - band_w + offset, ctx.h * 1.15),
                ]
            else:
                points = [
                    (x + offset, -ctx.h * 0.15),
                    (x + band_w + offset, -ctx.h * 0.15),
                    (x + band_w * 2 + offset, ctx.h * 1.15),
                    (x + band_w + offset, ctx.h * 1.15),
                ]

            ctx.draw.polygon(
                points,
                fill=(*ctx.accent, alpha),
            )
