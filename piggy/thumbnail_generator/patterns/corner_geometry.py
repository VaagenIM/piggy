"""Rounded corner-geometry ambient pattern."""

from .base import Pattern, PatternContext


class CornerGeometryPattern(Pattern):
    name = "corner_geometry"

    def draw(self, ctx: PatternContext) -> None:
        corners = [
            (0, 0, 1, 1),
            (ctx.w, 0, -1, 1),
            (0, ctx.h, 1, -1),
            (ctx.w, ctx.h, -1, -1),
        ]

        ctx.rng.shuffle(corners)

        for cx, cy, sx, sy in corners[:2]:
            size = ctx.rng.randint(
                int(min(ctx.w, ctx.h) * 0.14),
                int(min(ctx.w, ctx.h) * 0.26),
            )

            inset = size // 3
            x2 = cx + sx * size
            y2 = cy + sy * size

            ctx.draw.rounded_rectangle(
                (
                    min(cx, x2),
                    min(cy, y2),
                    max(cx, x2),
                    max(cy, y2),
                ),
                radius=max(8, size // 8),
                outline=(*ctx.accent, 75),
                width=max(2, ctx.w // 250),
            )

            ctx.draw.line(
                (
                    cx,
                    cy + sy * inset,
                    cx + sx * (size - inset),
                    cy + sy * size,
                ),
                fill=(*ctx.accent, 42),
                width=max(2, ctx.w // 300),
            )
