import math

from .base import Pattern, PatternContext


class TopographicContoursPattern(Pattern):
    name = "topographic_contours"

    def draw(
        self,
        ctx: PatternContext,
    ) -> None:
        side = ctx.rng.choice(
            ("left", "right")
        )

        center_x = (
            ctx.w * -0.04
            if side == "left"
            else ctx.w * 1.04
        )

        center_y = ctx.rng.uniform(
            ctx.h * 0.25,
            ctx.h * 0.75,
        )

        contour_count = ctx.rng.randint(
            5,
            8,
        )

        base_radius = ctx.rng.uniform(
            ctx.h * 0.12,
            ctx.h * 0.20,
        )

        gap = ctx.rng.uniform(
            ctx.h * 0.07,
            ctx.h * 0.11,
        )

        phase_a = ctx.rng.uniform(
            0,
            math.tau,
        )

        phase_b = ctx.rng.uniform(
            0,
            math.tau,
        )

        point_count = 90

        for contour in range(
            contour_count
        ):
            radius = (
                base_radius
                + contour * gap
            )

            points = []

            for i in range(
                point_count + 1
            ):
                angle = (
                    math.tau
                    * i
                    / point_count
                )

                wobble = (
                    math.sin(
                        angle * 3
                        + phase_a
                        + contour * 0.18
                    )
                    * radius
                    * 0.055
                    +
                    math.sin(
                        angle * 5
                        + phase_b
                        - contour * 0.12
                    )
                    * radius
                    * 0.025
                )

                r = radius + wobble

                x = (
                    center_x
                    + math.cos(angle) * r
                )

                y = (
                    center_y
                    + math.sin(angle) * r
                    * 0.70
                )

                points.append(
                    (x, y)
                )

            alpha = max(
                18,
                58 - contour * 5,
            )

            ctx.draw.line(
                points,
                fill=(
                    *ctx.accent,
                    alpha,
                ),
                width=max(
                    1,
                    ctx.w // 500,
                ),
            )
