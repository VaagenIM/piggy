"""Layered sine-wave ambient pattern."""

import math

from .base import Pattern, PatternContext


class WavesPattern(Pattern):
    name = "waves"

    def draw(self, ctx: PatternContext) -> None:
        count = ctx.rng.randint(3, 5)

        baseline = ctx.rng.choice(
            (
                int(ctx.h * 0.20),
                int(ctx.h * 0.78),
            )
        )

        for i in range(count):
            amplitude = ctx.rng.randint(
                max(10, ctx.h // 30),
                max(18, ctx.h // 16),
            )

            frequency = ctx.rng.uniform(0.006, 0.012)
            phase = ctx.rng.uniform(0, math.tau)

            y_base = baseline + i * max(8, ctx.h // 40)

            points = [
                (
                    x,
                    y_base + amplitude * math.sin(frequency * x + phase),
                )
                for x in range(
                    0,
                    ctx.w + 1,
                    max(3, ctx.w // 300),
                )
            ]

            ctx.draw.line(
                points,
                fill=(*ctx.accent, max(24, 65 - i * 8)),
                width=max(2, ctx.w // 350),
            )
