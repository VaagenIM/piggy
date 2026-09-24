"""Concentric edge-ring ambient pattern."""

from .base import Pattern, PatternContext


class RingsPattern(Pattern):
    name = "rings"

    def draw(self, ctx: PatternContext) -> None:
        width = max(2, ctx.w // 220)
        side = ctx.rng.choice(("left", "right"))

        if side == "right":
            cx = int(ctx.w * 0.92)
        else:
            cx = int(ctx.w * 0.08)

        cy = ctx.rng.randint(
            int(ctx.h * 0.10),
            int(ctx.h * 0.90),
        )

        gap = ctx.rng.randint(
            max(24, ctx.h // 12),
            max(34, ctx.h // 8),
        )

        for i in range(1, 6):
            radius = i * gap
            alpha = max(18, 90 - i * 12)

            ctx.draw.ellipse(
                (
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                ),
                outline=(*ctx.accent, alpha),
                width=width,
            )
