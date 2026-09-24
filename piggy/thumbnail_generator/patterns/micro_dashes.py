import math

from .base import Pattern, PatternContext


class MicroDashesPattern(Pattern):
    name = "micro_dashes"

    def draw(
        self,
        ctx: PatternContext,
    ) -> None:
        spacing_x = ctx.rng.randint(
            max(26, ctx.w // 38),
            max(38, ctx.w // 26),
        )

        spacing_y = ctx.rng.randint(
            max(24, ctx.h // 14),
            max(34, ctx.h // 10),
        )

        angle = ctx.rng.choice(
            (
                -35,
                -25,
                25,
                35,
            )
        )

        angle_rad = math.radians(angle)

        length = ctx.rng.uniform(
            max(5, ctx.h * 0.018),
            max(9, ctx.h * 0.032),
        )

        dx = math.cos(angle_rad) * length

        dy = math.sin(angle_rad) * length

        offset_x = ctx.rng.randint(
            0,
            spacing_x,
        )

        offset_y = ctx.rng.randint(
            0,
            spacing_y,
        )

        for row, y in enumerate(
            range(
                offset_y,
                ctx.h + spacing_y,
                spacing_y,
            )
        ):
            row_offset = spacing_x // 2 if row % 2 else 0

            for x in range(
                offset_x - row_offset,
                ctx.w + spacing_x,
                spacing_x,
            ):
                # Don't make this a perfectly uniform texture.
                if ctx.rng.random() < 0.28:
                    continue

                alpha = ctx.rng.randint(
                    20,
                    42,
                )

                ctx.draw.line(
                    (
                        x,
                        y,
                        x + dx,
                        y + dy,
                    ),
                    fill=(
                        *ctx.accent,
                        alpha,
                    ),
                    width=1,
                )
