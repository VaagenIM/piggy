"""Sparse graph-paper grid ambient pattern."""

from .base import Pattern, PatternContext


class GridPattern(Pattern):
    name = "grid"

    def draw(self, ctx: PatternContext) -> None:
        spacing = ctx.rng.randint(
            max(38, ctx.w // 24),
            max(52, ctx.w // 18),
        )

        alpha = ctx.rng.randint(20, 32)
        offset_x = ctx.rng.randint(0, spacing)
        offset_y = ctx.rng.randint(0, spacing)

        for x in range(offset_x, ctx.w, spacing):
            ctx.draw.line(
                (x, 0, x, ctx.h),
                fill=(*ctx.accent, alpha),
                width=1,
            )

        for y in range(offset_y, ctx.h, spacing):
            ctx.draw.line(
                (0, y, ctx.w, y),
                fill=(*ctx.accent, alpha),
                width=1,
            )

        # A few stronger points make the grid look intentional
        # rather than like plain graph paper.
        for _ in range(ctx.rng.randint(4, 8)):
            x = ctx.rng.randrange(
                offset_x,
                max(offset_x + 1, ctx.w),
                spacing,
            )

            y = ctx.rng.randrange(
                offset_y,
                max(offset_y + 1, ctx.h),
                spacing,
            )

            radius = max(3, min(ctx.w, ctx.h) // 120)

            ctx.draw.ellipse(
                (
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                ),
                fill=(*ctx.accent, 90),
            )
