from .base import Pattern, PatternContext


class BrokenGridPattern(Pattern):
    name = "broken_grid"

    def draw(
        self,
        ctx: PatternContext,
    ) -> None:
        cell = ctx.rng.randint(
            max(36, ctx.w // 26),
            max(54, ctx.w // 18),
        )

        offset_x = ctx.rng.randint(
            0,
            cell,
        )

        offset_y = ctx.rng.randint(
            0,
            cell,
        )

        segment_fraction = ctx.rng.uniform(
            0.30,
            0.68,
        )

        # Horizontal fragments
        for y in range(
            offset_y,
            ctx.h + cell,
            cell,
        ):
            for x in range(
                offset_x,
                ctx.w + cell,
                cell,
            ):
                if ctx.rng.random() > 0.55:
                    continue

                length = (
                    cell
                    * segment_fraction
                    * ctx.rng.uniform(
                        0.65,
                        1.15,
                    )
                )

                ctx.draw.line(
                    (
                        x,
                        y,
                        x + length,
                        y,
                    ),
                    fill=(
                        *ctx.accent,
                        ctx.rng.randint(
                            18,
                            38,
                        ),
                    ),
                    width=1,
                )

        # Vertical fragments
        for x in range(
            offset_x,
            ctx.w + cell,
            cell,
        ):
            for y in range(
                offset_y,
                ctx.h + cell,
                cell,
            ):
                if ctx.rng.random() > 0.55:
                    continue

                length = (
                    cell
                    * segment_fraction
                    * ctx.rng.uniform(
                        0.65,
                        1.15,
                    )
                )

                ctx.draw.line(
                    (
                        x,
                        y,
                        x,
                        y + length,
                    ),
                    fill=(
                        *ctx.accent,
                        ctx.rng.randint(
                            18,
                            38,
                        ),
                    ),
                    width=1,
                )

        # Rare brighter junctions.
        for _ in range(ctx.rng.randint(2, 6)):
            x = ctx.rng.randrange(
                offset_x,
                max(
                    offset_x + 1,
                    ctx.w,
                ),
                cell,
            )

            y = ctx.rng.randrange(
                offset_y,
                max(
                    offset_y + 1,
                    ctx.h,
                ),
                cell,
            )

            r = max(
                2,
                min(
                    ctx.w,
                    ctx.h,
                )
                // 150,
            )

            ctx.draw.ellipse(
                (
                    x - r,
                    y - r,
                    x + r,
                    y + r,
                ),
                fill=(
                    *ctx.accent,
                    70,
                ),
            )
